#!/usr/bin/env python3
"""
Test script for MemoryStorage system

This script tests the MemoryStorage functionality including:
- Job creation and retrieval
- Status updates and progress tracking
- Result storage and cleanup
- Automatic cleanup scheduler
- Memory optimization and statistics
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from memory_storage import MemoryStorage, JobData
from crew_manager import CrewProcessingResult


def test_job_creation():
    """Test basic job creation and retrieval"""
    print("=" * 60)
    print("Testing Job Creation and Retrieval")
    print("=" * 60)
    
    storage = MemoryStorage()
    
    # Test data
    test_file_data = b"Sample RTF contract content for testing"
    test_filename = "test_contract.rtf"
    test_prompt = "Change counterparty from ABC Corp to XYZ Ltd"
    
    # Create job
    job_id = storage.create_job(test_file_data, test_filename, test_prompt)
    print(f"✓ Created job: {job_id}")
    
    # Retrieve job
    job_data = storage.get_job(job_id)
    assert job_data is not None, "Job should exist"
    assert job_data.job_id == job_id, "Job ID should match"
    assert job_data.filename == test_filename, "Filename should match"
    assert job_data.user_prompt == test_prompt, "User prompt should match"
    assert job_data.file_data == test_file_data, "File data should match"
    assert job_data.status == "queued", "Initial status should be queued"
    assert job_data.progress == 0, "Initial progress should be 0"
    
    print(f"✓ Job data verified: {job_data.filename}, status={job_data.status}")
    
    # Test custom job ID
    custom_job_id = "custom-test-job-123"
    custom_job_id_result = storage.create_job(test_file_data, "custom.rtf", "test", custom_job_id)
    assert custom_job_id_result == custom_job_id, "Custom job ID should be used"
    
    print("✓ Custom job ID creation works")
    
    return True


def test_status_updates():
    """Test job status updates and progress tracking"""
    print("\n" + "=" * 60)
    print("Testing Status Updates and Progress Tracking")
    print("=" * 60)
    
    storage = MemoryStorage()
    
    # Create test job
    job_id = storage.create_job(b"test data", "test.rtf", "test prompt")
    
    # Test status updates
    test_cases = [
        ("processing", 25, None),
        ("processing", 50, None),
        ("processing", 75, None),
        ("completed", 100, None),
    ]
    
    for status, progress, error in test_cases:
        success = storage.update_job_status(job_id, status, progress, error)
        assert success, f"Status update should succeed for {status}"
        
        job_data = storage.get_job(job_id)
        assert job_data.status == status, f"Status should be {status}"
        assert job_data.progress == progress, f"Progress should be {progress}"
        
        print(f"✓ Updated to {status}: {progress}%")
    
    # Test error status
    error_job_id = storage.create_job(b"error test", "error.rtf", "error test")
    storage.update_job_status(error_job_id, "failed", 0, "Test error message")
    
    error_job = storage.get_job(error_job_id)
    assert error_job.status == "failed", "Status should be failed"
    assert error_job.error_message == "Test error message", "Error message should be set"
    
    print("✓ Error status handling works")
    
    # Test invalid job ID
    invalid_update = storage.update_job_status("invalid-job-id", "processing")
    assert not invalid_update, "Update should fail for invalid job ID"
    
    print("✓ Invalid job ID handling works")
    
    return True


def test_result_storage():
    """Test storing processing results"""
    print("\n" + "=" * 60)
    print("Testing Result Storage")
    print("=" * 60)
    
    storage = MemoryStorage()
    
    # Create test job
    job_id = storage.create_job(b"result test data", "result_test.rtf", "result test")
    
    # Create mock result
    mock_result = CrewProcessingResult(
        success=True,
        job_id=job_id,
        final_rtf="Modified RTF content here",
        original_rtf="Original RTF content",
        iterations_used=3,
        total_processing_time=45.5,
        final_score=0.92,
        crew_output="Processing completed successfully",
        error_message=None,
        chunk_processing_stats={"total_chunks": 5, "processed_chunks": 5}
    )
    
    # Store result
    success = storage.store_result(job_id, mock_result)
    assert success, "Result storage should succeed"
    
    # Verify result storage
    job_data = storage.get_job(job_id)
    assert job_data.result is not None, "Result should be stored"
    assert job_data.result.success == True, "Result success should match"
    assert job_data.result.final_rtf == "Modified RTF content here", "Final RTF should match"
    assert job_data.status == "completed", "Status should be completed"
    assert job_data.progress == 100, "Progress should be 100%"
    
    print(f"✓ Stored successful result: score={job_data.result.final_score}")
    
    # Test failed result
    failed_job_id = storage.create_job(b"failed test", "failed.rtf", "failed test")
    failed_result = CrewProcessingResult(
        success=False,
        job_id=failed_job_id,
        final_rtf=None,
        original_rtf="Original content",
        iterations_used=5,
        total_processing_time=30.0,
        final_score=0.65,
        crew_output="Processing failed",
        error_message="Quality threshold not met"
    )
    
    storage.store_result(failed_job_id, failed_result)
    failed_job = storage.get_job(failed_job_id)
    assert failed_job.status == "failed", "Status should be failed"
    assert failed_job.error_message == "Quality threshold not met", "Error message should be set"
    
    print("✓ Failed result handling works")
    
    return True


def test_job_status_api():
    """Test job status API response format"""
    print("\n" + "=" * 60)
    print("Testing Job Status API Response")
    print("=" * 60)
    
    storage = MemoryStorage()
    
    # Create and complete a job
    job_id = storage.create_job(b"api test data", "api_test.rtf", "api test prompt")
    storage.update_job_status(job_id, "processing", 50)
    
    # Test in-progress status
    status_info = storage.get_job_status(job_id)
    assert status_info is not None, "Status info should exist"
    assert status_info["job_id"] == job_id, "Job ID should match"
    assert status_info["status"] == "processing", "Status should match"
    assert status_info["progress"] == 50, "Progress should match"
    assert "created_at" in status_info, "Should include created_at"
    assert "updated_at" in status_info, "Should include updated_at"
    
    print(f"✓ In-progress status: {status_info['status']} ({status_info['progress']}%)")
    
    # Complete the job with result
    result = CrewProcessingResult(
        success=True,
        job_id=job_id,
        final_rtf="Final RTF content",
        original_rtf="Original RTF",
        iterations_used=2,
        total_processing_time=25.0,
        final_score=0.88,
        crew_output="Success",
        error_message=None,
        chunk_processing_stats={"total_chunks": 3, "processed_chunks": 3}
    )
    
    storage.store_result(job_id, result)
    
    # Test completed status
    completed_status = storage.get_job_status(job_id)
    assert completed_status["status"] == "completed", "Status should be completed"
    assert completed_status["progress"] == 100, "Progress should be 100%"
    assert "result_rtf" in completed_status, "Should include result RTF"
    assert "final_score" in completed_status, "Should include final score"
    assert "iterations_used" in completed_status, "Should include iterations"
    assert "processing_time" in completed_status, "Should include processing time"
    assert "chunk_stats" in completed_status, "Should include chunk stats"
    
    print(f"✓ Completed status: score={completed_status['final_score']}")
    
    # Test invalid job ID
    invalid_status = storage.get_job_status("invalid-job-id")
    assert invalid_status is None, "Invalid job should return None"
    
    print("✓ Invalid job ID handling works")
    
    return True


def test_cleanup_operations():
    """Test job cleanup and automatic cleanup"""
    print("\n" + "=" * 60)
    print("Testing Cleanup Operations")
    print("=" * 60)
    
    storage = MemoryStorage(max_age_hours=1, cleanup_interval_minutes=1)
    
    # Create test jobs
    job_ids = []
    for i in range(3):
        job_id = storage.create_job(f"test data {i}".encode(), f"test_{i}.rtf", f"test prompt {i}")
        job_ids.append(job_id)
    
    print(f"✓ Created {len(job_ids)} test jobs")
    
    # Test manual cleanup
    cleanup_success = storage.cleanup_job(job_ids[0])
    assert cleanup_success, "Manual cleanup should succeed"
    
    remaining_job = storage.get_job(job_ids[0])
    assert remaining_job is None, "Cleaned up job should not exist"
    
    print("✓ Manual cleanup works")
    
    # Test cleanup of non-existent job
    invalid_cleanup = storage.cleanup_job("invalid-job-id")
    assert not invalid_cleanup, "Cleanup of invalid job should fail"
    
    # Create old job by manipulating timestamp
    old_job_id = storage.create_job(b"old job data", "old.rtf", "old prompt")
    old_job = storage.get_job(old_job_id)
    old_job.created_at = datetime.now() - timedelta(hours=2)  # Make it old
    
    # Test automatic cleanup
    cleaned_count = storage.auto_cleanup()
    assert cleaned_count >= 1, "Should clean up at least the old job"
    
    cleaned_job = storage.get_job(old_job_id)
    assert cleaned_job is None, "Old job should be cleaned up"
    
    print(f"✓ Auto cleanup removed {cleaned_count} jobs")
    
    return True


def test_storage_statistics():
    """Test storage statistics and memory tracking"""
    print("\n" + "=" * 60)
    print("Testing Storage Statistics")
    print("=" * 60)
    
    storage = MemoryStorage()
    
    # Create jobs with different statuses
    job_data = [
        (b"queued job data", "queued.rtf", "queued", "queued"),
        (b"processing job data", "processing.rtf", "processing", "processing"),
        (b"completed job data", "completed.rtf", "completed", "completed"),
        (b"failed job data", "failed.rtf", "failed", "failed"),
    ]
    
    job_ids = []
    for data, filename, prompt, status in job_data:
        job_id = storage.create_job(data, filename, prompt)
        if status != "queued":
            storage.update_job_status(job_id, status)
        job_ids.append(job_id)
    
    # Get statistics
    stats = storage.get_storage_stats()
    
    assert stats["total_jobs"] == len(job_data), f"Should have {len(job_data)} jobs"
    assert "status_counts" in stats, "Should include status counts"
    assert "total_memory_bytes" in stats, "Should include memory usage"
    assert "total_memory_mb" in stats, "Should include memory in MB"
    
    print(f"✓ Total jobs: {stats['total_jobs']}")
    print(f"✓ Status counts: {stats['status_counts']}")
    print(f"✓ Memory usage: {stats['total_memory_mb']} MB")
    print(f"✓ Cleanup config: {stats['max_age_hours']}h interval, {stats['cleanup_interval_minutes']}min cleanup")
    
    return True


def test_thread_safety():
    """Test thread safety of memory storage operations"""
    print("\n" + "=" * 60)
    print("Testing Thread Safety")
    print("=" * 60)
    
    storage = MemoryStorage()
    results = []
    errors = []
    
    def worker_thread(thread_id):
        """Worker thread that creates and updates jobs"""
        try:
            for i in range(5):
                # Create job
                job_id = storage.create_job(
                    f"thread {thread_id} job {i}".encode(),
                    f"thread_{thread_id}_job_{i}.rtf",
                    f"thread {thread_id} prompt {i}"
                )
                
                # Update status
                storage.update_job_status(job_id, "processing", 50)
                storage.update_job_status(job_id, "completed", 100)
                
                results.append(job_id)
                
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    # Start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"No errors should occur: {errors}"
    assert len(results) == 15, "Should have 15 jobs created (3 threads × 5 jobs)"
    
    # Verify all jobs exist and are completed
    completed_count = 0
    for job_id in results:
        job_data = storage.get_job(job_id)
        assert job_data is not None, f"Job {job_id} should exist"
        if job_data.status == "completed":
            completed_count += 1
    
    assert completed_count == 15, "All jobs should be completed"
    
    print(f"✓ Thread safety test passed: {len(results)} jobs created, {completed_count} completed")
    
    return True


def main():
    """Run all memory storage tests"""
    print("Memory Storage System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Job Creation Test", test_job_creation),
        ("Status Updates Test", test_status_updates),
        ("Result Storage Test", test_result_storage),
        ("Job Status API Test", test_job_status_api),
        ("Cleanup Operations Test", test_cleanup_operations),
        ("Storage Statistics Test", test_storage_statistics),
        ("Thread Safety Test", test_thread_safety),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Memory storage system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)