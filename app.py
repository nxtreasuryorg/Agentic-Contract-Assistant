"""
Contract Assistant vNext - API Server

Flask API server for Contract-Agent microservice with CrewAI integration.
Based on nxtChat server.py pattern with contract-specific enhancements.
"""

import os
import uuid
import json
import time
import threading
import queue
from datetime import datetime, timedelta
from io import BytesIO
from collections import defaultdict
import fitz  # PyMuPDF for PDF processing
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import Contract-Agent modules
from core.crew.crew_manager import ContractProcessingCrew
from core.types import CrewProcessingResult
from infrastructure.storage.memory_storage import MemoryStorage
from infrastructure.aws.bedrock_client import BedrockModelManager
from core.document_processing import pdf_utils
from core.utils.monitoring import get_monitor

# Load environment variables
load_dotenv()

# Configure Flask with increased max content length and timeouts for large contracts
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB for large contracts
app.config['JSON_AS_ASCII'] = False  # Properly handle Unicode
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for large files

# Enable CORS for nxtApp integration
CORS(app, origins=["*"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])

# Initialize paths first
script_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(script_dir, "data", "uploads")
RTF_OUTPUT_FOLDER = os.path.join(script_dir, "data", "generated")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RTF_OUTPUT_FOLDER, exist_ok=True)

# Validate critical configuration
def validate_configuration():
    """Validate critical configuration before starting server"""
    issues = []
    
    # Check AWS region
    if not os.getenv('AWS_REGION_NAME'):
        issues.append("AWS_REGION_NAME not set")
    
    # Check model configuration
    if not os.getenv('CONTRACT_PRIMARY_MODEL'):
        issues.append("CONTRACT_PRIMARY_MODEL not set")
    
    # Check if upload directories are writable
    try:
        test_file = os.path.join(UPLOAD_FOLDER, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        issues.append(f"Upload folder not writable: {e}")
    
    if issues:
        print("❌ Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        print("Please fix configuration issues before starting the server.")
        return False
    
    print("✅ Configuration validation passed")
    return True

# Initialize Contract-Agent components
print("🚀 Initializing Contract-Agent API Server...")

# Validate configuration first
if not validate_configuration():
    exit(1)

memory_storage = MemoryStorage()
crew_manager = ContractProcessingCrew()
bedrock_manager = BedrockModelManager()

# Job processing queue and background thread
job_queue = queue.Queue()
processing_thread = None
job_lock = threading.Lock()

# Rate limiting disabled for comprehensive testing
# rate_limit_requests = defaultdict(list)  # IP -> list of timestamps
# rate_limit_lock = threading.Lock()
# MAX_REQUESTS_PER_HOUR = 20  # Limit to 20 contract processing requests per hour per IP

print(f"📁 Upload folder: {UPLOAD_FOLDER}")
print(f"📁 RTF output folder: {RTF_OUTPUT_FOLDER}")
print(f"🔥 Bedrock integration: {bedrock_manager is not None}")


def start_processing_thread():
    """Start the background job processing thread"""
    global processing_thread
    
    def process_jobs():
        """Background thread function to process contract jobs"""
        print("🔄 Contract processing thread started")
        
        while True:
            try:
                # Get job from queue (blocking) - no timeout, wait indefinitely
                job_id, user_prompt, file_path, original_filename = job_queue.get(block=True)
                
                print(f"📋 Processing job {job_id}: {original_filename}")
                
                # Start monitoring
                monitor = get_monitor()
                monitor.start_job(job_id, file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0, 
                                prompt_length=len(user_prompt))
                
                # Update job status to processing
                memory_storage.update_job_status(job_id, "processing", 10)
                
                # Extract text from PDF
                original_rtf = extract_text_from_file(file_path)
                if not original_rtf:
                    memory_storage.update_job_status(
                        job_id, "failed", 0, 
                        "Failed to extract text from document"
                    )
                    continue
                
                memory_storage.update_job_status(job_id, "processing", 30)
                
                # Process contract with CrewAI workflow - with retry logic
                print(f"🤖 Starting CrewAI processing for job {job_id}")
                max_retries = 2
                result = None
                
                for attempt in range(1, max_retries + 1):
                    try:
                        if attempt > 1:
                            monitor.increment_retry(job_id)
                        memory_storage.update_job_status(job_id, "processing", 30 + (attempt * 10))
                        result = crew_manager.process_contract(
                            original_rtf=original_rtf,
                            user_prompt=user_prompt,
                            job_id=job_id
                        )
                        break  # Success, exit retry loop
                    except Exception as retry_error:
                        print(f"⚠️ Attempt {attempt} failed: {retry_error}")
                        if attempt == max_retries:
                            # Final attempt failed, create error result
                            from core.types import CrewProcessingResult
                            result = CrewProcessingResult(
                                success=False,
                                job_id=job_id,
                                final_rtf=None,
                                original_rtf=original_rtf,
                                iterations_used=0,
                                total_processing_time=0,
                                final_score=0,
                                crew_output="",
                                error_message=f"Processing failed after {max_retries} attempts: {str(retry_error)}"
                            )
                        else:
                            # Wait before retry
                            time.sleep(5)
                
                # Store result in memory
                memory_storage.store_result(job_id, result)
                
                if result.success:
                    memory_storage.update_job_status(job_id, "completed", 100)
                    monitor.complete_job(job_id, True, quality_score=result.final_score, 
                                       iterations=result.iterations_used)
                    print(f"✅ Job {job_id} completed successfully")
                else:
                    memory_storage.update_job_status(
                        job_id, "failed", 0, 
                        result.error_message or "Processing failed"
                    )
                    monitor.complete_job(job_id, False, error_message=result.error_message)
                    print(f"❌ Job {job_id} failed: {result.error_message}")
                
                # Clean up temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            except queue.Empty:
                # This shouldn't happen with block=True, but handle gracefully
                time.sleep(1)
                continue
            except Exception as e:
                print(f"💥 Processing thread error: {e}")
                # Mark job as failed if we have job_id
                try:
                    if 'job_id' in locals():
                        memory_storage.update_job_status(
                            job_id, "failed", 0, 
                            f"Processing error: {str(e)}"
                        )
                except:
                    pass
    
    processing_thread = threading.Thread(target=process_jobs, daemon=True)
    processing_thread.start()
    return processing_thread


def extract_text_from_file(file_path: str) -> str:
    """Extract text content from uploaded file"""
    try:
        if file_path.lower().endswith('.pdf'):
            # Extract text from PDF using PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        else:
            # Assume text file
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for nxtApp monitoring"""
    try:
        # Check component status
        bedrock_available = bedrock_manager.test_connection() if hasattr(bedrock_manager, 'test_connection') else True
        crew_available = crew_manager is not None
        processing_thread_alive = processing_thread.is_alive() if processing_thread else False
        
        return jsonify({
            "status": "healthy",
            "message": "Contract-Agent is running with CrewAI integration",
            "components": {
                "bedrock_available": bedrock_available,
                "crewai_available": crew_available,
                "processing_thread_active": processing_thread_alive,
                "memory_storage_active": memory_storage is not None
            },
            "queue_size": job_queue.qsize(),
            "performance_metrics": get_monitor().get_statistics(),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/process_contract', methods=['POST'])
def process_contract():
    """
    Process contract document with user prompt through CrewAI workflow.
    Handles file upload + prompt from nxtApp with chunking support.
    """
    try:
        # Rate limiting disabled for comprehensive testing
        # client_ip = request.remote_addr or "unknown"
        # if not check_rate_limit(client_ip):
        #     return jsonify({
        #         "error": f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_HOUR} requests per hour.",
        #         "success": False
        #     }), 429
        
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                "error": "No file provided",
                "success": False
            }), 400
        
        file = request.files['file']
        user_prompt = request.form.get('prompt', '').strip()
        
        if not file or file.filename == '':
            return jsonify({
                "error": "No file selected",
                "success": False
            }), 400
        
        if not user_prompt:
            return jsonify({
                "error": "No modification prompt provided",
                "success": False
            }), 400
        
        # Enhanced file validation for security
        allowed_extensions = {'.pdf', '.txt', '.rtf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                "error": f"Unsupported file type: {file_ext}. Supported: {', '.join(allowed_extensions)}",
                "success": False
            }), 400
        
        # Validate file size
        if file.content_length and file.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({
                "error": "File too large. Maximum size is 200MB.",
                "success": False
            }), 413
        
        # Validate prompt length and content
        if len(user_prompt) > 10000:  # Reasonable limit for prompts
            return jsonify({
                "error": "Prompt too long. Maximum 10,000 characters.",
                "success": False
            }), 400
        
        # Basic prompt sanitization
        if any(char in user_prompt for char in ['<script>', '</script>', 'javascript:', 'data:']):
            return jsonify({
                "error": "Invalid characters in prompt.",
                "success": False
            }), 400
        
        # Generate job ID and save file
        job_id = str(uuid.uuid4())
        filename = f"{job_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save uploaded file
        file.save(file_path)
        
        # Create job in memory storage
        file_data = open(file_path, 'rb').read()
        memory_storage.create_job(
            file_data=file_data,
            filename=file.filename,
            user_prompt=user_prompt,
            job_id=job_id
        )
        
        # Add job to processing queue
        job_queue.put((job_id, user_prompt, file_path, file.filename))
        
        # Check if processing thread is alive
        if not processing_thread or not processing_thread.is_alive():
            print("⚠️ Processing thread is dead, restarting...")
            start_processing_thread()
        
        print(f"📨 Job {job_id} queued: {file.filename} with prompt: {user_prompt[:100]}...")
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Contract processing job queued successfully",
            "filename": file.filename,
            "prompt": user_prompt,
            "success": True
        }), 202
        
    except Exception as e:
        print(f"Error in process_contract: {e}")
        return jsonify({
            "error": f"Failed to process contract: {str(e)}",
            "success": False
        }), 500


# Rate limiting disabled for comprehensive testing
# def check_rate_limit(client_ip: str) -> bool:
#     """Check if client IP has exceeded rate limit"""
#     with rate_limit_lock:
#         now = datetime.now()
#         hour_ago = now - timedelta(hours=1)
#         
#         # Clean old requests
#         rate_limit_requests[client_ip] = [
#             req_time for req_time in rate_limit_requests[client_ip] 
#             if req_time > hour_ago
#         ]
#         
#         # Check if under limit
#         if len(rate_limit_requests[client_ip]) >= MAX_REQUESTS_PER_HOUR:
#             return False
#         
#         # Add current request
#         rate_limit_requests[client_ip].append(now)
#         return True

def validate_job_id(job_id: str) -> bool:
    """Validate job ID format for security"""
    try:
        # Check for empty or None
        if not job_id or not job_id.strip():
            return False
        
        # Check for path traversal attempts
        if ".." in job_id or "/" in job_id or "\\" in job_id:
            return False
        
        # Check for HTML/script tags
        if "<" in job_id or ">" in job_id:
            return False
        
        # Check if it's a valid UUID format
        uuid.UUID(job_id)
        return True
    except (ValueError, TypeError):
        return False

@app.route('/job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Get processing status and results for a job.
    Returns status, progress, and final RTF if completed.
    """
    try:
        # Validate job ID format
        if not validate_job_id(job_id):
            return jsonify({
                "error": "Invalid job ID format",
                "success": False
            }), 400
        
        # Get job data from memory storage
        job_data = memory_storage.get_job(job_id)
        
        if not job_data:
            return jsonify({
                "error": "Job not found",
                "success": False
            }), 404
        
        response = {
            "job_id": job_id,
            "status": job_data.status,
            "progress": job_data.progress,
            "message": f"Job {job_data.status}",
            "filename": job_data.filename,
            "user_prompt": job_data.user_prompt,
            "created_at": job_data.created_at.isoformat(),
            "updated_at": job_data.updated_at.isoformat(),
            "success": True
        }
        
        # Include results if job is completed
        if job_data.status == "completed" and job_data.result:
            result = job_data.result
            response.update({
                "final_rtf": result.final_rtf,
                "iterations_used": result.iterations_used,
                "processing_time": result.total_processing_time,
                "final_score": result.final_score,
                "chunk_stats": result.chunk_processing_stats
            })
        
        # Include error message if failed
        if job_data.status == "failed":
            response["error_message"] = job_data.error_message
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error getting job status for {job_id}: {e}")
        return jsonify({
            "error": f"Failed to get job status: {str(e)}",
            "success": False
        }), 500


@app.route('/job_result/<job_id>', methods=['GET'])
def get_job_result(job_id):
    """
    Get the complete result of a completed job with full RTF content.
    Returns detailed processing results and metrics.
    """
    try:
        # Validate job ID format
        if not validate_job_id(job_id):
            return jsonify({
                "error": "Invalid job ID format",
                "success": False
            }), 400
        
        job_data = memory_storage.get_job(job_id)
        
        if not job_data:
            return jsonify({
                "error": "Job not found",
                "success": False
            }), 404
        
        if job_data.status != "completed":
            return jsonify({
                "job_id": job_id,
                "status": job_data.status,
                "progress": job_data.progress,
                "message": "Job not completed yet",
                "success": False
            }), 202
        
        if not job_data.result:
            return jsonify({
                "error": "Job completed but no result found",
                "success": False
            }), 500
        
        result = job_data.result
        
        response_data = {
            "job_id": job_id,
            "status": "completed",
            "filename": job_data.filename,
            "user_prompt": job_data.user_prompt,
            "processing_results": {
                "success": result.success,
                "final_rtf": result.final_rtf,
                "original_rtf": result.original_rtf[:1000] + "..." if len(result.original_rtf) > 1000 else result.original_rtf,
                "iterations_used": result.iterations_used,
                "total_processing_time": result.total_processing_time,
                "final_score": result.final_score,
                "crew_output": result.crew_output[:500] + "..." if len(result.crew_output) > 500 else result.crew_output,
                "chunk_processing_stats": result.chunk_processing_stats
            },
            "created_at": job_data.created_at.isoformat(),
            "updated_at": job_data.updated_at.isoformat(),
            "success": True
        }
        
        # Trigger session-based cleanup after result retrieval
        if hasattr(memory_storage, 'session_based_cleanup') and memory_storage.session_based_cleanup:
            cleanup_success = memory_storage.cleanup_completed_job_after_retrieval(job_id)
            if cleanup_success:
                print(f"🧹 Session cleanup completed for job {job_id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error getting job result for {job_id}: {e}")
        return jsonify({
            "error": f"Failed to get job result: {str(e)}",
            "success": False
        }), 500


@app.route('/debug/queue', methods=['GET'])
def debug_queue():
    """Debug endpoint to check processing queue and job status"""
    try:
        # Get queue status
        queue_size = job_queue.qsize()
        thread_alive = processing_thread.is_alive() if processing_thread else False
        
        # Get job statistics from memory storage
        job_stats = memory_storage.get_job_statistics() if hasattr(memory_storage, 'get_job_statistics') else {}
        
        return jsonify({
            "queue_size": queue_size,
            "processing_thread_alive": thread_alive,
            "job_statistics": job_stats,
            "memory_storage_active": memory_storage is not None,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Debug queue failed: {str(e)}"
        }), 500


@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics and statistics"""
    try:
        monitor = get_monitor()
        stats = monitor.get_statistics()
        recent_failures = monitor.get_recent_failures(5)
        
        return jsonify({
            "success": True,
            "statistics": stats,
            "recent_failures": recent_failures,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get metrics: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/debug/test_crewai', methods=['POST'])
def test_crewai():
    """Debug endpoint to test CrewAI workflow directly"""
    try:
        data = request.get_json()
        test_rtf = data.get('test_rtf', 'This is a test contract with ABC Corporation.')
        test_prompt = data.get('test_prompt', 'Change ABC Corporation to XYZ Limited')
        
        print(f"🧪 Testing CrewAI workflow...")
        
        result = crew_manager.process_contract(
            original_rtf=test_rtf,
            user_prompt=test_prompt,
            job_id="debug-test"
        )
        
        return jsonify({
            "test_successful": result.success,
            "result": {
                "final_rtf": result.final_rtf,
                "iterations_used": result.iterations_used,
                "processing_time": result.total_processing_time,
                "final_score": result.final_score,
                "error_message": result.error_message
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "test_successful": False,
            "error": f"CrewAI test failed: {str(e)}"
        }), 500


# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "File too large. Maximum size is 200MB.",
        "success": False
    }), 413


# Rate limiting error handler disabled
# @app.errorhandler(429)
# def rate_limit_exceeded(error):
#     return jsonify({
#         "error": f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_HOUR} requests per hour.",
#         "success": False
#     }), 429


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": "Internal server error occurred",
        "success": False
    }), 500


# Initialize and start server
if __name__ == '__main__':
    print("🚀 Starting Contract-Agent API Server...")
    
    # Start job processing thread
    start_processing_thread()
    print(f"✅ Processing thread started: {processing_thread is not None}")
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5002))
    print(f"🌐 Contract-Agent API listening on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
