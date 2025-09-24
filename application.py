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
from datetime import datetime
from io import BytesIO
import fitz  # PyMuPDF for PDF processing
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import Contract-Agent modules
from core.crew.crew_manager import ContractProcessingCrew
from core.types import CrewProcessingResult
from infrastructure.storage.memory_storage import MemoryStorage
from infrastructure.aws.bedrock_client import BedrockModelManager
from core.document_processing import pdf_utils

# Load environment variables
load_dotenv()

# Configure Flask with increased max content length and timeouts for large contracts
# Use 'application' name for EB compatibility
application = Flask(__name__)
application.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB for large contracts
application.config['JSON_AS_ASCII'] = False  # Properly handle Unicode
application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for large files

# Initialize Contract-Agent components
print("🚀 Initializing Contract-Agent API Server...")
memory_storage = MemoryStorage()
crew_manager = ContractProcessingCrew()
bedrock_manager = BedrockModelManager()

# Initialize paths
script_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(script_dir, "data", "uploads")
RTF_OUTPUT_FOLDER = os.path.join(script_dir, "data", "generated")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RTF_OUTPUT_FOLDER, exist_ok=True)

# Job processing queue and background thread
job_queue = queue.Queue()
processing_thread = None
job_lock = threading.Lock()

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
                # Get job from queue (blocking) - increased timeout for large contract processing
                job_id, user_prompt, file_path, original_filename = job_queue.get(timeout=120)
                
                print(f"📋 Processing job {job_id}: {original_filename}")
                
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
                
                # Process contract with CrewAI workflow
                print(f"🤖 Starting CrewAI processing for job {job_id}")
                result = crew_manager.process_contract(
                    original_rtf=original_rtf,
                    user_prompt=user_prompt,
                    job_id=job_id
                )
                
                # Store result in memory
                memory_storage.store_result(job_id, result)
                
                if result.success:
                    memory_storage.update_job_status(job_id, "completed", 100)
                    print(f"✅ Job {job_id} completed successfully")
                else:
                    memory_storage.update_job_status(
                        job_id, "failed", 0, 
                        result.error_message or "Processing failed"
                    )
                    print(f"❌ Job {job_id} failed: {result.error_message}")
                
                # Clean up temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            except queue.Empty:
                # No jobs in queue, continue waiting
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


# Root route for Elastic Beanstalk health checks
@application.route('/', methods=['GET'])
def root():
    """Root endpoint for EB health checks."""
    return jsonify({
        "status": "healthy", 
        "service": "Contract-Agent vNext",
        "message": "Contract Assistant API is running with CrewAI integration",
        "version": "1.0.0",
        "endpoints": ["/health", "/process_contract", "/job_status", "/job_result"]
    })


@application.route('/health', methods=['GET'])
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
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@application.route('/process_contract', methods=['POST'])
def process_contract():
    """
    Process contract document with user prompt through CrewAI workflow.
    Handles file upload + prompt from nxtApp with chunking support.
    """
    try:
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
        
        # Validate file type
        allowed_extensions = {'.pdf', '.txt', '.rtf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                "error": f"Unsupported file type: {file_ext}. Supported: {', '.join(allowed_extensions)}",
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


@application.route('/job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Get processing status and results for a job.
    Returns status, progress, and final RTF if completed.
    """
    try:
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


@application.route('/job_result/<job_id>', methods=['GET'])
def get_job_result(job_id):
    """
    Get the complete result of a completed job with full RTF content.
    Returns detailed processing results and metrics.
    """
    try:
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


@application.route('/debug/queue', methods=['GET'])
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


@application.route('/debug/test_crewai', methods=['POST'])
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
@application.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "File too large. Maximum size is 200MB.",
        "success": False
    }), 413


@application.errorhandler(500)
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
    
    application.run(host='0.0.0.0', port=port, debug=False)
