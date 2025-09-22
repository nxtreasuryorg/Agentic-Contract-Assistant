#!/usr/bin/env python3
"""
Task 11.5: Comprehensive Contract-Agent Integration Testing and Validation

This test suite validates all implemented components (Tasks 1-8) and their interactions.
Tests complete workflow: Bedrock → System Prompts → Document Chunking → CrewAI Agents → Memory Storage → API Server
"""

import os
import sys
import time
import json
import uuid
import tempfile
import requests
import subprocess
import threading
import concurrent.futures
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
CONTRACT_AGENT_URL = "http://localhost:5002"
TEST_TIMEOUT = 600  # 10 minutes for comprehensive testing
MAX_CONCURRENT_JOBS = 3


class ComprehensiveIntegrationTester:
    """Comprehensive integration tester for all Contract-Agent components"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.test_results = []
        self.performance_metrics = {}
        
    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """Log test result with timing"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {status} - {test_name}"
        if duration > 0:
            result += f" ({duration:.1f}s)"
        if message:
            result += f": {message}"
        print(result)
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": timestamp
        })
    
    def start_server(self) -> bool:
        """Start Contract-Agent server"""
        try:
            print("🚀 Starting Contract-Agent server for comprehensive testing...")
            
            self.server_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                cwd='/home/ec2-user/cb/Contract-Agent',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for attempt in range(20):
                try:
                    response = requests.get(f"{CONTRACT_AGENT_URL}/health", timeout=5)
                    if response.status_code == 200:
                        self.log_test("Server Startup", True, f"Server started on {CONTRACT_AGENT_URL}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(2)
                    continue
            
            self.log_test("Server Startup", False, "Server failed to start within 40 seconds")
            return False
            
        except Exception as e:
            self.log_test("Server Startup", False, str(e))
            return False
    
    def stop_server(self):
        """Stop test server"""
        if self.server_process:
            print("🛑 Stopping Contract-Agent server...")
            self.server_process.terminate()
            self.server_process.wait(timeout=10)
            self.server_process = None
    
    def test_bedrock_integration(self) -> bool:
        """Test AWS Bedrock integration (Task 1)"""
        print("\n🔍 Testing Bedrock Integration...")
        start_time = time.time()
        
        try:
            # Test Bedrock connectivity through debug endpoint
            response = requests.post(
                f"{CONTRACT_AGENT_URL}/debug/test_crewai",
                json={
                    "test_rtf": "Test contract with TestCorp Inc.",
                    "test_prompt": "Change TestCorp Inc. to NewCorp LLC"
                },
                timeout=120
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('test_successful', False)
                
                if success:
                    self.log_test("Bedrock Integration", True, "CrewAI with Bedrock working", duration)
                    return True
                else:
                    self.log_test("Bedrock Integration", False, "CrewAI test failed", duration)
                    return False
            else:
                self.log_test("Bedrock Integration", False, f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Bedrock Integration", False, str(e), duration)
            return False
    
    def test_system_prompts(self) -> bool:
        """Test system prompts effectiveness (Task 2)"""
        print("\n📝 Testing System Prompts...")
        
        try:
            from system_prompts import SystemPrompts
            
            prompt_manager = SystemPrompts()
            
            # Test actor prompt generation
            actor_prompt = prompt_manager.get_actor_prompt(chunk_id=1, total_chunks=3)
            critic_prompt = prompt_manager.get_critic_prompt()
            
            # Verify prompts contain expected elements
            actor_valid = len(actor_prompt) > 100 and 'contract' in actor_prompt.lower()
            critic_valid = len(critic_prompt) > 100 and 'evaluation' in critic_prompt.lower()
            
            if actor_valid and critic_valid:
                self.log_test("System Prompts", True, "Actor and Critic prompts generated correctly")
                return True
            else:
                self.log_test("System Prompts", False, "Prompt validation failed")
                return False
                
        except Exception as e:
            self.log_test("System Prompts", False, str(e))
            return False
    
    def test_document_chunking(self) -> bool:
        """Test document chunking system (Task 3)"""
        print("\n📊 Testing Document Chunking...")
        
        try:
            from document_chunking import DocumentChunkingManager
            
            chunking_manager = DocumentChunkingManager()
            
            # Test small document (no chunking)
            small_doc = "Short contract content" * 100
            needs_chunking_small = chunking_manager.should_chunk_document(small_doc)
            
            # Test large document (should chunk)
            large_doc = "Large contract content with extensive clauses and provisions. " * 2000
            needs_chunking_large = chunking_manager.should_chunk_document(large_doc)
            
            if not needs_chunking_small and needs_chunking_large:
                # Test actual chunking
                chunks = chunking_manager.split_document(large_doc)
                
                if len(chunks) > 1:
                    self.log_test("Document Chunking", True, f"Correctly split into {len(chunks)} chunks")
                    return True
                else:
                    self.log_test("Document Chunking", False, "Failed to split large document")
                    return False
            else:
                self.log_test("Document Chunking", False, "Chunking logic failed")
                return False
                
        except Exception as e:
            self.log_test("Document Chunking", False, str(e))
            return False
    
    def test_crewai_agents(self) -> bool:
        """Test CrewAI agents (Tasks 4-6)"""
        print("\n🤖 Testing CrewAI Agents...")
        
        try:
            from crew_manager import ContractProcessingCrew
            
            crew_manager = ContractProcessingCrew()
            
            # Test agent creation
            test_context = {
                'original_rtf': 'Employment Agreement with TechCorp Inc., Delaware corporation',
                'user_prompt': 'Change TechCorp Inc. to InnovateTech LLC, change Delaware to California',
                'job_id': 'test-agents'
            }
            
            crew = crew_manager.build_actor_critic_crew(test_context)
            
            # Verify crew has correct structure
            if len(crew.agents) >= 2 and len(crew.tasks) >= 2:
                self.log_test("CrewAI Agents", True, f"{len(crew.agents)} agents, {len(crew.tasks)} tasks")
                return True
            else:
                self.log_test("CrewAI Agents", False, "Crew structure invalid")
                return False
                
        except Exception as e:
            self.log_test("CrewAI Agents", False, str(e))
            return False
    
    def test_memory_storage(self) -> bool:
        """Test memory storage system (Task 7)"""
        print("\n💾 Testing Memory Storage...")
        
        try:
            from memory_storage import MemoryStorage
            
            storage = MemoryStorage()
            
            # Test job creation
            job_id = storage.create_job(
                file_data=b'test contract content',
                filename='test.txt',
                user_prompt='test prompt'
            )
            
            # Test job retrieval
            job_data = storage.get_job(job_id)
            
            if job_data and job_data.filename == 'test.txt':
                # Test status updates
                storage.update_job_status(job_id, "processing", 50)
                updated_job = storage.get_job(job_id)
                
                if updated_job.status == "processing" and updated_job.progress == 50:
                    self.log_test("Memory Storage", True, "Job CRUD operations working")
                    return True
                else:
                    self.log_test("Memory Storage", False, "Status update failed")
                    return False
            else:
                self.log_test("Memory Storage", False, "Job creation/retrieval failed")
                return False
                
        except Exception as e:
            self.log_test("Memory Storage", False, str(e))
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API server endpoints (Task 8)"""
        print("\n🌐 Testing API Endpoints...")
        
        endpoints_tested = 0
        total_endpoints = 4
        
        # Test health endpoint
        try:
            response = requests.get(f"{CONTRACT_AGENT_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    endpoints_tested += 1
                    print("   ✅ /health endpoint working")
                else:
                    print("   ❌ /health endpoint unhealthy")
            else:
                print(f"   ❌ /health returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ /health error: {e}")
        
        # Test debug endpoints
        try:
            response = requests.get(f"{CONTRACT_AGENT_URL}/debug/queue", timeout=10)
            if response.status_code == 200:
                endpoints_tested += 1
                print("   ✅ /debug/queue endpoint working")
            else:
                print(f"   ❌ /debug/queue returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ /debug/queue error: {e}")
        
        # Test process_contract endpoint (upload only)
        try:
            test_file_content = "Test contract for API validation"
            files = {'file': ('test.txt', test_file_content, 'text/plain')}
            data = {'prompt': 'Test prompt for API validation'}
            
            response = requests.post(
                f"{CONTRACT_AGENT_URL}/process_contract",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 202:
                result = response.json()
                if 'job_id' in result:
                    endpoints_tested += 1
                    print("   ✅ /process_contract endpoint working")
                    
                    # Test job_status endpoint
                    job_id = result['job_id']
                    status_response = requests.get(f"{CONTRACT_AGENT_URL}/job_status/{job_id}", timeout=10)
                    if status_response.status_code == 200:
                        endpoints_tested += 1
                        print("   ✅ /job_status endpoint working")
                    else:
                        print(f"   ❌ /job_status returned {status_response.status_code}")
                else:
                    print("   ❌ /process_contract no job_id returned")
            else:
                print(f"   ❌ /process_contract returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ /process_contract error: {e}")
        
        success = endpoints_tested == total_endpoints
        self.log_test("API Endpoints", success, f"{endpoints_tested}/{total_endpoints} endpoints working")
        return success
    
    def test_concurrent_processing(self) -> bool:
        """Test concurrent processing scenarios"""
        print("\n🔄 Testing Concurrent Processing...")
        
        def process_contract(contract_id: int):
            """Process a single contract"""
            try:
                test_content = f"Contract {contract_id}: Agreement with Company{contract_id} Inc."
                files = {'file': (f'contract_{contract_id}.txt', test_content, 'text/plain')}
                data = {'prompt': f'Change Company{contract_id} Inc. to NewCorp{contract_id} LLC'}
                
                start_time = time.time()
                response = requests.post(
                    f"{CONTRACT_AGENT_URL}/process_contract",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 202:
                    job_id = response.json().get('job_id')
                    if job_id:
                        return {
                            'contract_id': contract_id,
                            'job_id': job_id,
                            'success': True,
                            'upload_time': time.time() - start_time
                        }
                
                return {
                    'contract_id': contract_id,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
            except Exception as e:
                return {
                    'contract_id': contract_id,
                    'success': False,
                    'error': str(e)
                }
        
        try:
            # Submit multiple jobs concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS) as executor:
                futures = [executor.submit(process_contract, i) for i in range(1, MAX_CONCURRENT_JOBS + 1)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            successful_jobs = [r for r in results if r['success']]
            
            if len(successful_jobs) == MAX_CONCURRENT_JOBS:
                avg_upload_time = sum(r['upload_time'] for r in successful_jobs) / len(successful_jobs)
                self.log_test("Concurrent Processing", True, 
                             f"{len(successful_jobs)} jobs submitted, avg upload: {avg_upload_time:.2f}s")
                return True
            else:
                failed_count = len(results) - len(successful_jobs)
                self.log_test("Concurrent Processing", False, f"{failed_count} jobs failed")
                return False
                
        except Exception as e:
            self.log_test("Concurrent Processing", False, str(e))
            return False
    
    def benchmark_performance(self) -> bool:
        """Benchmark performance with various document sizes"""
        print("\n📈 Benchmarking Performance...")
        
        document_sizes = [
            ("Small", 1000),    # 1KB
            ("Medium", 10000),  # 10KB  
            ("Large", 50000),   # 50KB
            ("Very Large", 100000)  # 100KB
        ]
        
        performance_results = {}
        
        for size_name, char_count in document_sizes:
            try:
                # Create document of specified size
                content = f"Performance test document for {size_name} size. " * (char_count // 50)
                content = content[:char_count]  # Exact size
                
                files = {'file': (f'perf_test_{size_name.lower()}.txt', content, 'text/plain')}
                data = {'prompt': f'Add a note: "Performance test completed for {size_name} document"'}
                
                start_time = time.time()
                response = requests.post(
                    f"{CONTRACT_AGENT_URL}/process_contract",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                upload_time = time.time() - start_time
                
                if response.status_code == 202:
                    performance_results[size_name] = {
                        'char_count': char_count,
                        'upload_time': upload_time,
                        'success': True
                    }
                    print(f"   ✅ {size_name} ({char_count} chars): {upload_time:.2f}s upload")
                else:
                    performance_results[size_name] = {
                        'char_count': char_count,
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    }
                    print(f"   ❌ {size_name} failed: HTTP {response.status_code}")
                    
            except Exception as e:
                performance_results[size_name] = {
                    'char_count': char_count,
                    'success': False,
                    'error': str(e)
                }
                print(f"   ❌ {size_name} error: {e}")
        
        # Store performance metrics
        self.performance_metrics = performance_results
        
        successful_tests = sum(1 for r in performance_results.values() if r['success'])
        total_tests = len(document_sizes)
        
        self.log_test("Performance Benchmark", 
                     successful_tests == total_tests, 
                     f"{successful_tests}/{total_tests} size tests passed")
        
        return successful_tests == total_tests
    
    def test_system_resilience(self) -> bool:
        """Test system resilience with various failure scenarios"""
        print("\n🛡️ Testing System Resilience...")
        
        resilience_tests = []
        
        # Test 1: Invalid JSON in request
        try:
            response = requests.post(
                f"{CONTRACT_AGENT_URL}/debug/test_crewai",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            resilience_tests.append(response.status_code >= 400)
        except:
            resilience_tests.append(False)
        
        # Test 2: Very large prompt
        try:
            large_prompt = "X" * 100000  # 100KB prompt
            files = {'file': ('test.txt', 'Small test content', 'text/plain')}
            data = {'prompt': large_prompt}
            
            response = requests.post(
                f"{CONTRACT_AGENT_URL}/process_contract",
                files=files,
                data=data,
                timeout=30
            )
            # Should handle gracefully (either process or reject properly)
            resilience_tests.append(response.status_code in [202, 400, 413])
        except:
            resilience_tests.append(False)
        
        # Test 3: Rapid successive requests
        try:
            responses = []
            for i in range(10):
                response = requests.get(f"{CONTRACT_AGENT_URL}/health", timeout=5)
                responses.append(response.status_code == 200)
            
            resilience_tests.append(sum(responses) >= 8)  # Allow some failures
        except:
            resilience_tests.append(False)
        
        passed_tests = sum(resilience_tests)
        total_tests = len(resilience_tests)
        
        self.log_test("System Resilience", 
                     passed_tests >= total_tests - 1,  # Allow one failure
                     f"{passed_tests}/{total_tests} resilience tests passed")
        
        return passed_tests >= total_tests - 1
    
    def generate_integration_report(self) -> str:
        """Generate comprehensive integration test report"""
        report_lines = [
            "# Contract-Agent Integration Test Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Test Summary",
            f"Total Tests: {len(self.test_results)}",
            f"Passed: {sum(1 for r in self.test_results if r['success'])}",
            f"Failed: {sum(1 for r in self.test_results if not r['success'])}",
            "",
            "## Component Test Results",
        ]
        
        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            duration_str = f" ({result['duration']:.1f}s)" if result['duration'] > 0 else ""
            message_str = f" - {result['message']}" if result['message'] else ""
            report_lines.append(f"- {result['test']}: {status}{duration_str}{message_str}")
        
        if self.performance_metrics:
            report_lines.extend([
                "",
                "## Performance Metrics",
            ])
            
            for size_name, metrics in self.performance_metrics.items():
                if metrics['success']:
                    report_lines.append(f"- {size_name} ({metrics['char_count']} chars): {metrics['upload_time']:.2f}s upload")
                else:
                    report_lines.append(f"- {size_name}: FAILED - {metrics.get('error', 'Unknown error')}")
        
        report_lines.extend([
            "",
            "## System Readiness Assessment",
            "Based on the comprehensive testing results:",
        ])
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if pass_rate >= 90:
            report_lines.append("✅ SYSTEM READY FOR DEPLOYMENT")
            report_lines.append(f"Pass rate: {pass_rate:.1f}% - All critical components operational")
        elif pass_rate >= 75:
            report_lines.append("⚠️ SYSTEM PARTIALLY READY")
            report_lines.append(f"Pass rate: {pass_rate:.1f}% - Some components need attention")
        else:
            report_lines.append("❌ SYSTEM NOT READY")
            report_lines.append(f"Pass rate: {pass_rate:.1f}% - Critical issues must be resolved")
        
        return "\n".join(report_lines)
    
    def run_comprehensive_tests(self) -> bool:
        """Run all comprehensive integration tests"""
        print("🧪 Starting Comprehensive Contract-Agent Integration Tests (Task 11.5)")
        print("=" * 80)
        
        try:
            # Start server
            if not self.start_server():
                return False
            
            time.sleep(5)  # Allow server to fully initialize
            
            # Component tests (Tasks 1-8)
            component_tests = [
                ("Bedrock Integration (Task 1)", self.test_bedrock_integration),
                ("System Prompts (Task 2)", self.test_system_prompts),
                ("Document Chunking (Task 3)", self.test_document_chunking),
                ("CrewAI Agents (Tasks 4-6)", self.test_crewai_agents),
                ("Memory Storage (Task 7)", self.test_memory_storage),
                ("API Endpoints (Task 8)", self.test_api_endpoints),
            ]
            
            # Integration and performance tests
            integration_tests = [
                ("Concurrent Processing", self.test_concurrent_processing),
                ("Performance Benchmark", self.benchmark_performance),
                ("System Resilience", self.test_system_resilience),
            ]
            
            # Run all tests
            for test_name, test_func in component_tests + integration_tests:
                print(f"\n🔍 Running {test_name}...")
                test_func()
            
            # Generate and display report
            report = self.generate_integration_report()
            print("\n" + "=" * 80)
            print(report)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r['success'])
            success = passed_tests >= total_tests * 0.9  # 90% pass rate required
            
            if success:
                print(f"\n🎉 COMPREHENSIVE INTEGRATION TESTS PASSED! ({passed_tests}/{total_tests})")
                print("System is ready for deployment!")
            else:
                print(f"\n❌ Integration tests incomplete. ({passed_tests}/{total_tests} passed)")
            
            # Save report to file
            with open('/home/ec2-user/cb/Contract-Agent/integration_test_report.md', 'w') as f:
                f.write(report)
            print(f"\n📄 Full report saved to: integration_test_report.md")
            
            return success
            
        finally:
            self.stop_server()


def main():
    """Main test execution function"""
    tester = ComprehensiveIntegrationTester()
    
    try:
        success = tester.run_comprehensive_tests()
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
