#!/usr/bin/env python3
"""
Contract Assistant vNext - API Server Test Script

Test script to verify the Contract-Agent API server functionality.
Tests all endpoints and CrewAI integration with sample contract processing.
"""

import os
import sys
import time
import json
import requests
import threading
import subprocess
from typing import Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
API_BASE_URL = "http://localhost:5002"
TEST_TIMEOUT = 120  # 2 minutes timeout for processing


class ContractAgentTester:
    """Test class for Contract-Agent API server"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.server_process: Optional[subprocess.Popen] = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {status} - {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append({"test": test_name, "success": success, "message": message})
        
    def start_server(self) -> bool:
        """Start the Contract-Agent API server"""
        try:
            print("🚀 Starting Contract-Agent API server...")
            
            # Start server in background
            contract_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.server_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=contract_agent_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for attempt in range(10):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        self.log_test("Server Startup", True, f"Server started on {self.base_url}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(2)
                    continue
            
            self.log_test("Server Startup", False, "Server failed to start within 20 seconds")
            return False
            
        except Exception as e:
            self.log_test("Server Startup", False, str(e))
            return False
    
    def stop_server(self):
        """Stop the API server"""
        if self.server_process:
            print("🛑 Stopping Contract-Agent API server...")
            self.server_process.terminate()
            self.server_process.wait(timeout=10)
            self.server_process = None
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "healthy"
                message = f"Status: {data.get('status')}, Components: {data.get('components', {})}"
                self.log_test("Health Endpoint", success, message)
                return success
            else:
                self.log_test("Health Endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False
    
    def create_test_contract(self) -> str:
        """Create a test contract file"""
        test_content = """
        EMPLOYMENT AGREEMENT
        
        This Employment Agreement is entered into between TechCorp Inc., a Delaware corporation 
        (the "Company"), and John Smith (the "Employee").
        
        1. EMPLOYMENT: Company hereby employs Employee as a Software Engineer.
        
        2. COMPENSATION: Company shall pay Employee a base salary of $100,000 per year.
        
        3. BENEFITS: Employee shall be entitled to standard company benefits.
        
        4. GOVERNING LAW: This Agreement shall be governed by the laws of Delaware.
        
        5. LIABILITY: Company shall indemnify Employee against all work-related claims.
        
        6. TERMINATION: Either party may terminate this agreement with 30 days notice.
        
        IN WITNESS WHEREOF, the parties have executed this Agreement.
        
        TechCorp Inc.
        By: _________________
        CEO
        
        Employee: _________________
        John Smith
        """
        
        test_file_path = "test_contract.txt"
        with open(test_file_path, 'w') as f:
            f.write(test_content.strip())
        
        return test_file_path
    
    def test_contract_processing(self) -> bool:
        """Test contract processing workflow"""
        try:
            # Create test contract
            test_file_path = self.create_test_contract()
            
            # Test prompt
            test_prompt = "Change company name from TechCorp Inc. to InnovateTech LLC and change governing law from Delaware to California"
            
            # Upload and process contract
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_contract.txt', f, 'text/plain')}
                data = {'prompt': test_prompt}
                
                response = requests.post(
                    f"{self.base_url}/process_contract",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 202:
                self.log_test("Contract Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            job_id = result.get('job_id')
            
            if not job_id:
                self.log_test("Contract Upload", False, "No job_id returned")
                return False
            
            self.log_test("Contract Upload", True, f"Job ID: {job_id}")
            
            # Poll for completion
            return self.poll_job_completion(job_id)
            
        except Exception as e:
            self.log_test("Contract Processing", False, str(e))
            return False
        finally:
            # Cleanup test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def poll_job_completion(self, job_id: str) -> bool:
        """Poll job status until completion"""
        start_time = time.time()
        
        while time.time() - start_time < TEST_TIMEOUT:
            try:
                response = requests.get(f"{self.base_url}/job_status/{job_id}", timeout=10)
                
                if response.status_code != 200:
                    self.log_test("Job Status Check", False, f"HTTP {response.status_code}")
                    return False
                
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', 0)
                
                print(f"   📊 Job {job_id}: {status} ({progress}%)")
                
                if status == 'completed':
                    self.log_test("Job Completion", True, f"Completed in {time.time() - start_time:.1f}s")
                    return self.test_job_result(job_id)
                elif status == 'failed':
                    error_msg = data.get('error_message', 'Unknown error')
                    self.log_test("Job Completion", False, f"Job failed: {error_msg}")
                    return False
                
                time.sleep(5)  # Wait 5 seconds before next poll
                
            except Exception as e:
                self.log_test("Job Polling", False, str(e))
                return False
        
        self.log_test("Job Completion", False, f"Timeout after {TEST_TIMEOUT}s")
        return False
    
    def test_job_result(self, job_id: str) -> bool:
        """Test getting full job result"""
        try:
            response = requests.get(f"{self.base_url}/job_result/{job_id}", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Job Result", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            processing_results = data.get('processing_results', {})
            final_rtf = processing_results.get('final_rtf', '')
            final_score = processing_results.get('final_score', 0)
            iterations = processing_results.get('iterations_used', 0)
            
            # Verify the contract was modified
            success = (
                'InnovateTech LLC' in final_rtf and
                'California' in final_rtf and
                final_score >= 0.85
            )
            
            message = f"Score: {final_score}, Iterations: {iterations}, RTF length: {len(final_rtf)}"
            self.log_test("Job Result", success, message)
            
            if success:
                print(f"   📄 Contract successfully modified:")
                print(f"      • TechCorp Inc. → InnovateTech LLC: {'✅' if 'InnovateTech LLC' in final_rtf else '❌'}")
                print(f"      • Delaware → California: {'✅' if 'California' in final_rtf else '❌'}")
            
            return success
            
        except Exception as e:
            self.log_test("Job Result", False, str(e))
            return False
    
    def test_debug_endpoints(self) -> bool:
        """Test debug endpoints"""
        try:
            # Test queue debug endpoint
            response = requests.get(f"{self.base_url}/debug/queue", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Debug Queue", True, f"Queue size: {data.get('queue_size', 0)}")
            else:
                self.log_test("Debug Queue", False, f"HTTP {response.status_code}")
                return False
            
            # Test CrewAI debug endpoint
            test_data = {
                "test_rtf": "Test contract with ABC Corp.",
                "test_prompt": "Change ABC Corp to XYZ Ltd"
            }
            
            response = requests.post(
                f"{self.base_url}/debug/test_crewai",
                json=test_data,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('test_successful', False)
                self.log_test("CrewAI Debug", success, f"Test result: {success}")
                return success
            else:
                self.log_test("CrewAI Debug", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Debug Endpoints", False, str(e))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all API tests"""
        print("🧪 Starting Contract-Agent API Server Tests")
        print("=" * 60)
        
        try:
            # Start server
            if not self.start_server():
                return False
            
            time.sleep(3)  # Give server time to fully initialize
            
            # Run tests
            tests_passed = 0
            total_tests = 4
            
            if self.test_health_endpoint():
                tests_passed += 1
            
            if self.test_debug_endpoints():
                tests_passed += 1
            
            if self.test_contract_processing():
                tests_passed += 1
            
            # Test error handling
            try:
                response = requests.get(f"{self.base_url}/job_status/nonexistent", timeout=10)
                error_handling_ok = response.status_code == 404
                self.log_test("Error Handling", error_handling_ok, f"404 for nonexistent job")
                if error_handling_ok:
                    tests_passed += 1
            except:
                self.log_test("Error Handling", False, "Exception testing error handling")
            
            # Print summary
            print("\n" + "=" * 60)
            print(f"📊 TEST SUMMARY: {tests_passed}/{total_tests} tests passed")
            
            if tests_passed == total_tests:
                print("🎉 ALL TESTS PASSED! Contract-Agent API server is working correctly.")
                return True
            else:
                print("❌ Some tests failed. Check logs above for details.")
                return False
                
        finally:
            self.stop_server()


def main():
    """Main test function"""
    tester = ContractAgentTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        tester.stop_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        tester.stop_server()
        sys.exit(1)


if __name__ == "__main__":
    main()
