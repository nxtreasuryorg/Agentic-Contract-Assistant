"""
Contract Assistant vNext - Memory Storage Manager

This module manages temporary file storage in memory with automatic cleanup.
Handles processing results and intermediate data for contract processing workflow.
"""

import threading
import time
import uuid
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging
from threading import Lock
from crew_manager import CrewProcessingResult


@dataclass
class JobData:
    """Data structure for storing job information"""
    job_id: str
    file_data: Optional[bytes]
    filename: str
    user_prompt: str
    status: str  # queued, processing, completed, failed
    created_at: datetime
    updated_at: datetime
    result: Optional[CrewProcessingResult] = None
    progress: int = 0  # 0-100
    error_message: Optional[str] = None


class MemoryStorage:
    """
    Manages temporary file storage in memory with automatic cleanup.
    Thread-safe implementation for concurrent job processing.
    """
    
    def __init__(self, max_age_hours: int = 24, cleanup_interval_minutes: int = 60):
        """
        Initialize memory storage with cleanup configuration.
        
        Args:
            max_age_hours: Maximum age for jobs before cleanup (default: 24 hours)
            cleanup_interval_minutes: Cleanup check interval (default: 60 minutes)
        """
        self.storage: Dict[str, JobData] = {}
        self.max_age_hours = max_age_hours
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self._lock = Lock()
        self._cleanup_running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup scheduler
        self._start_cleanup_scheduler()
    
    def create_job(self, 
                   file_data: bytes, 
                   filename: str, 
                   user_prompt: str, 
                   job_id: str = None) -> str:
        """
        Create a new job and store file in memory.
        
        Args:
            file_data: Binary file content
            filename: Original filename
            user_prompt: User instructions for processing
            job_id: Optional custom job ID
            
        Returns:
            Job ID for tracking processing
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        with self._lock:
            job_data = JobData(
                job_id=job_id,
                file_data=file_data,
                filename=filename,
                user_prompt=user_prompt,
                status="queued",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                progress=0
            )
            
            self.storage[job_id] = job_data
            self.logger.info(f"Created job {job_id} for file {filename}")
            
        return job_id
    
    def get_job(self, job_id: str) -> Optional[JobData]:
        """
        Retrieve job data by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobData if found, None otherwise
        """
        with self._lock:
            return self.storage.get(job_id)
    
    def update_job_status(self, 
                         job_id: str, 
                         status: str, 
                         progress: int = None,
                         error_message: str = None) -> bool:
        """
        Update job status and progress.
        
        Args:
            job_id: Job identifier
            status: New status (queued, processing, completed, failed)
            progress: Progress percentage (0-100)
            error_message: Error message if status is failed
            
        Returns:
            True if update successful, False if job not found
        """
        with self._lock:
            job_data = self.storage.get(job_id)
            if not job_data:
                return False
            
            job_data.status = status
            job_data.updated_at = datetime.now()
            
            if progress is not None:
                job_data.progress = min(100, max(0, progress))
            
            if error_message:
                job_data.error_message = error_message
            
            self.logger.info(f"Updated job {job_id}: status={status}, progress={job_data.progress}%")
            return True
    
    def store_result(self, job_id: str, result: CrewProcessingResult) -> bool:
        """
        Store processing results for completed job.
        
        Args:
            job_id: Job identifier
            result: CrewProcessingResult from contract processing
            
        Returns:
            True if storage successful, False if job not found
        """
        with self._lock:
            job_data = self.storage.get(job_id)
            if not job_data:
                return False
            
            job_data.result = result
            job_data.status = "completed" if result.success else "failed"
            job_data.progress = 100
            job_data.updated_at = datetime.now()
            
            if not result.success:
                job_data.error_message = result.error_message
            
            self.logger.info(f"Stored result for job {job_id}: success={result.success}")
            return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status information for API response.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Status dictionary or None if job not found
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return None
        
        status_info = {
            "job_id": job_data.job_id,
            "status": job_data.status,
            "progress": job_data.progress,
            "created_at": job_data.created_at.isoformat(),
            "updated_at": job_data.updated_at.isoformat()
        }
        
        # Add result RTF if completed successfully
        if job_data.status == "completed" and job_data.result and job_data.result.success:
            status_info["result_rtf"] = job_data.result.final_rtf
            status_info["final_score"] = job_data.result.final_score
            status_info["iterations_used"] = job_data.result.iterations_used
            status_info["processing_time"] = job_data.result.total_processing_time
            
            if job_data.result.chunk_processing_stats:
                status_info["chunk_stats"] = job_data.result.chunk_processing_stats
        
        # Add error information if failed
        if job_data.status == "failed":
            status_info["error_message"] = job_data.error_message or "Processing failed"
        
        return status_info
    
    def cleanup_job(self, job_id: str) -> bool:
        """
        Remove job and all associated data.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cleanup successful, False if job not found
        """
        with self._lock:
            if job_id in self.storage:
                job_data = self.storage.pop(job_id)
                self.logger.info(f"Cleaned up job {job_id} ({job_data.filename})")
                return True
            return False
    
    def auto_cleanup(self) -> int:
        """
        Automatic cleanup of old jobs based on age.
        
        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        cleaned_count = 0
        
        with self._lock:
            jobs_to_remove = []
            
            for job_id, job_data in self.storage.items():
                if job_data.created_at < cutoff_time:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                self.storage.pop(job_id)
                cleaned_count += 1
                
        if cleaned_count > 0:
            self.logger.info(f"Auto-cleanup removed {cleaned_count} expired jobs")
            
        return cleaned_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get current storage statistics.
        
        Returns:
            Dictionary with storage metrics
        """
        with self._lock:
            total_jobs = len(self.storage)
            
            status_counts = {}
            total_size = 0
            
            for job_data in self.storage.values():
                status = job_data.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if job_data.file_data:
                    total_size += len(job_data.file_data)
            
            return {
                "total_jobs": total_jobs,
                "status_counts": status_counts,
                "total_memory_bytes": total_size,
                "total_memory_mb": round(total_size / (1024 * 1024), 2),
                "cleanup_interval_minutes": self.cleanup_interval_minutes,
                "max_age_hours": self.max_age_hours
            }
    
    def _start_cleanup_scheduler(self):
        """Start the background cleanup scheduler"""
        if self._cleanup_running:
            return
            
        def cleanup_worker():
            while self._cleanup_running:
                try:
                    self.auto_cleanup()
                    time.sleep(self.cleanup_interval_minutes * 60)
                except Exception as e:
                    self.logger.error(f"Cleanup scheduler error: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        self._cleanup_running = True
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        
        self.logger.info(f"Started cleanup scheduler: cleanup every {self.cleanup_interval_minutes} minutes")
    
    def stop_cleanup_scheduler(self):
        """Stop the cleanup scheduler"""
        self._cleanup_running = False
        self.logger.info("Stopped cleanup scheduler")
    
    def __del__(self):
        """Ensure cleanup scheduler is stopped on object destruction"""
        self.stop_cleanup_scheduler()


# Global memory storage instance
_memory_storage = MemoryStorage()

def get_memory_storage() -> MemoryStorage:
    """Get the global memory storage instance"""
    return _memory_storage

def create_job(file_data: bytes, filename: str, user_prompt: str, job_id: str = None) -> str:
    """Convenience function to create a job"""
    return _memory_storage.create_job(file_data, filename, user_prompt, job_id)

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get job status"""
    return _memory_storage.get_job_status(job_id)
