"""
Contract-Agent Performance Monitoring and Metrics

This module provides monitoring capabilities for tracking job processing,
performance metrics, and error patterns.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading

@dataclass
class JobMetrics:
    """Metrics for a single job"""
    job_id: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "pending"
    processing_time: Optional[float] = None
    iterations: int = 0
    quality_score: Optional[float] = None
    error_message: Optional[str] = None
    file_size: int = 0
    prompt_length: int = 0
    retry_count: int = 0
    chunk_count: int = 0


class PerformanceMonitor:
    """Monitor and track Contract-Agent performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, JobMetrics] = {}
        self.error_counts = defaultdict(int)
        self.success_count = 0
        self.failure_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def start_job(self, job_id: str, file_size: int = 0, prompt_length: int = 0) -> None:
        """Record job start"""
        with self.lock:
            self.metrics[job_id] = JobMetrics(
                job_id=job_id,
                start_time=time.time(),
                status="processing",
                file_size=file_size,
                prompt_length=prompt_length
            )
            
    def update_job(self, job_id: str, **kwargs) -> None:
        """Update job metrics"""
        with self.lock:
            if job_id in self.metrics:
                for key, value in kwargs.items():
                    if hasattr(self.metrics[job_id], key):
                        setattr(self.metrics[job_id], key, value)
                        
    def complete_job(self, job_id: str, success: bool, 
                    quality_score: Optional[float] = None,
                    iterations: int = 0,
                    error_message: Optional[str] = None) -> None:
        """Mark job as complete"""
        with self.lock:
            if job_id in self.metrics:
                job = self.metrics[job_id]
                job.end_time = time.time()
                job.processing_time = job.end_time - job.start_time
                job.status = "completed" if success else "failed"
                job.quality_score = quality_score
                job.iterations = iterations
                job.error_message = error_message
                
                if success:
                    self.success_count += 1
                else:
                    self.failure_count += 1
                    if error_message:
                        # Track error patterns
                        if "timeout" in error_message.lower():
                            self.error_counts["timeout"] += 1
                        elif "extract" in error_message.lower():
                            self.error_counts["extraction"] += 1
                        elif "crew" in error_message.lower():
                            self.error_counts["crewai"] += 1
                        else:
                            self.error_counts["other"] += 1
                            
    def increment_retry(self, job_id: str) -> None:
        """Increment retry count for a job"""
        with self.lock:
            if job_id in self.metrics:
                self.metrics[job_id].retry_count += 1
                
    def get_statistics(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        with self.lock:
            total_jobs = len(self.metrics)
            if total_jobs == 0:
                return {
                    "total_jobs": 0,
                    "success_rate": 0,
                    "avg_processing_time": 0,
                    "avg_quality_score": 0,
                    "error_breakdown": {},
                    "uptime_hours": 0
                }
                
            completed_jobs = [m for m in self.metrics.values() if m.processing_time is not None]
            successful_jobs = [m for m in completed_jobs if m.status == "completed"]
            
            avg_processing_time = sum(j.processing_time for j in completed_jobs) / len(completed_jobs) if completed_jobs else 0
            avg_quality_score = sum(j.quality_score for j in successful_jobs if j.quality_score) / len(successful_jobs) if successful_jobs else 0
            
            # Calculate percentiles for processing time
            if completed_jobs:
                processing_times = sorted([j.processing_time for j in completed_jobs])
                p50_time = processing_times[len(processing_times) // 2]
                p95_time = processing_times[int(len(processing_times) * 0.95)] if len(processing_times) > 1 else processing_times[0]
            else:
                p50_time = p95_time = 0
                
            return {
                "total_jobs": total_jobs,
                "completed_jobs": len(completed_jobs),
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": self.success_count / total_jobs if total_jobs > 0 else 0,
                "avg_processing_time": avg_processing_time,
                "p50_processing_time": p50_time,
                "p95_processing_time": p95_time,
                "avg_quality_score": avg_quality_score,
                "error_breakdown": dict(self.error_counts),
                "uptime_hours": (time.time() - self.start_time) / 3600,
                "active_jobs": len([m for m in self.metrics.values() if m.status == "processing"])
            }
            
    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failed jobs for debugging"""
        with self.lock:
            failed_jobs = [m for m in self.metrics.values() if m.status == "failed"]
            failed_jobs.sort(key=lambda x: x.start_time, reverse=True)
            return [asdict(job) for job in failed_jobs[:limit]]
            
    def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON file"""
        with self.lock:
            data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.get_statistics(),
                "recent_failures": self.get_recent_failures(),
                "all_metrics": [asdict(m) for m in self.metrics.values()]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.metrics.clear()
            self.error_counts.clear()
            self.success_count = 0
            self.failure_count = 0
            self.start_time = time.time()


# Global monitor instance
_monitor = PerformanceMonitor()

def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _monitor
