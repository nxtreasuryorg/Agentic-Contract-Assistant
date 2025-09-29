#!/usr/bin/env python3
"""
Security and Reliability Test Suite for Contract-Agent

This script tests all the security fixes and reliability improvements
that were implemented during the codebase review.
"""

import requests
import json
import time
import uuid
from pathlib import Path
import sys

# Test configuration
BASE_URL = "http://localhost:5002"
TEST_FILE_CONTENT = "This is a test contract with ABC Corporation."

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Health endpoint working correctly")
                return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("🔍 Testing rate limiting...")
    
    # Create a small test file
    test_file_path = Path("/tmp/test_contract.txt")
    test_file_path.write_text(TEST_FILE_CONTENT)
    
    success_count = 0
    rate_limited = False
    
    # Try to make multiple requests rapidly
    for i in range(25):  # More than the limit of 20
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': f}
                data = {'prompt': f'Test prompt {i}'}
                
                response = requests.post(f"{BASE_URL}/process_contract", 
                                       files=files, data=data)
                
                if response.status_code == 429:
                    print(f"✅ Rate limiting activated after {success_count} requests")
                    rate_limited = True
                    break
                elif response.status_code == 202:
                    success_count += 1
                    
        except Exception as e:
            print(f"Request {i} failed: {e}")
    
    # Wait for rate limit to reset
    if rate_limited:
        print("⏳ Waiting for rate limit to reset...")
        time.sleep(65)  # Wait for rate limit window to reset
    
    # Cleanup
    test_file_path.unlink()
    
    if rate_limited and success_count <= 10:
        print("✅ Rate limiting working correctly")
        return True
    else:
        print(f"❌ Rate limiting not working. Success count: {success_count}")
        return False

def test_input_validation():
    """Test input validation and security checks"""
    print("🔍 Testing input validation...")
    
    test_cases = [
        # Test missing file
        {
            "name": "Missing file",
            "files": None,
            "data": {"prompt": "test"},
            "expected_status": 400
        },
        # Test invalid file type
        {
            "name": "Invalid file type",
            "content": TEST_FILE_CONTENT,
            "filename": "test.exe",
            "data": {"prompt": "test"},
            "expected_status": 400
        },
        # Test empty prompt
        {
            "name": "Empty prompt",
            "content": TEST_FILE_CONTENT,
            "filename": "test.txt",
            "data": {"prompt": ""},
            "expected_status": 400
        },
        # Test very long prompt
        {
            "name": "Long prompt",
            "content": TEST_FILE_CONTENT,
            "filename": "test.txt",
            "data": {"prompt": "x" * 15000},  # Exceeds 10k limit
            "expected_status": 400
        },
        # Test malicious prompt
        {
            "name": "Malicious prompt",
            "content": TEST_FILE_CONTENT,
            "filename": "test.txt",
            "data": {"prompt": "Change <script>alert('xss')</script>"},
            "expected_status": 400
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            if test_case.get("content"):
                # Create temporary file
                test_file = Path(f"/tmp/{test_case['filename']}")
                test_file.write_text(test_case["content"])
                
                with open(test_file, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(f"{BASE_URL}/process_contract",
                                           files=files, data=test_case["data"])
                
                test_file.unlink()
            else:
                response = requests.post(f"{BASE_URL}/process_contract",
                                       data=test_case["data"])
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['name']}: Correctly rejected")
                passed += 1
            else:
                print(f"❌ {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: Exception occurred: {e}")
    
    print(f"Input validation: {passed}/{total} tests passed")
    return passed == total

def test_job_id_validation():
    """Test job ID validation"""
    print("🔍 Testing job ID validation...")
    
    invalid_job_ids = [
        "invalid-id",
        "12345",
        "../../../etc/passwd",
        "<script>alert('xss')</script>",
        "null",
        ""
    ]
    
    passed = 0
    total = len(invalid_job_ids)
    
    for job_id in invalid_job_ids:
        try:
            response = requests.get(f"{BASE_URL}/job_status/{job_id}")
            if response.status_code == 400:
                print(f"✅ Invalid job ID '{job_id}' correctly rejected")
                passed += 1
            else:
                print(f"❌ Invalid job ID '{job_id}' not rejected (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Job ID test failed: {e}")
    
    print(f"Job ID validation: {passed}/{total} tests passed")
    return passed == total

def test_cors_headers():
    """Test CORS configuration"""
    print("🔍 Testing CORS headers...")
    
    try:
        # Test OPTIONS request
        response = requests.options(f"{BASE_URL}/health")
        headers = response.headers
        
        cors_checks = [
            ("Access-Control-Allow-Origin" in headers, "CORS origin header"),
            ("Access-Control-Allow-Methods" in headers, "CORS methods header"),
            ("Access-Control-Allow-Headers" in headers, "CORS headers header")
        ]
        
        passed = sum(1 for check, _ in cors_checks if check)
        total = len(cors_checks)
        
        for check, name in cors_checks:
            if check:
                print(f"✅ {name} present")
            else:
                print(f"❌ {name} missing")
        
        print(f"CORS configuration: {passed}/{total} checks passed")
        return passed == total
        
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and responses"""
    print("🔍 Testing error handling...")
    
    try:
        # Test 404 endpoint
        response = requests.get(f"{BASE_URL}/nonexistent")
        if response.status_code == 404:
            print("✅ 404 handling working")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            return False
        
        # Test malformed request
        response = requests.post(f"{BASE_URL}/process_contract", 
                               data="invalid json", 
                               headers={"Content-Type": "application/json"})
        if response.status_code in [400, 422]:
            print("✅ Malformed request handling working")
        else:
            print(f"❌ Malformed request not handled properly: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all security and reliability tests"""
    print("🔒 Contract-Agent Security & Reliability Test Suite")
    print("=" * 60)
    
    # Check if server is running
    if not test_health_endpoint():
        print("❌ Server not available. Please start the Contract-Agent server first.")
        sys.exit(1)
    
    tests = [
        ("Rate Limiting", test_rate_limiting),
        ("Input Validation", test_input_validation),
        ("Job ID Validation", test_job_id_validation),
        ("CORS Headers", test_cors_headers),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 SECURITY TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SECURITY TESTS PASSED!")
        print("✅ The Contract-Agent is secure and reliable.")
    else:
        print("⚠️  Some security tests failed.")
        print("🔧 Please review and fix the identified issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
