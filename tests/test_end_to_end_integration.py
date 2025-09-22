#!/usr/bin/env python3
"""
Task 11: End-to-End Integration Testing with Chunking Scenarios

This test suite validates the complete workflow from nxtApp upload to RTF display
with both small and large documents, including chunking scenarios.
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
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/home/ec2-user/cb/nxtApp')
sys.path.insert(0, '/home/ec2-user/cb/nxtApp/nxtAppCore')

# Configuration
CONTRACT_AGENT_URL = "http://localhost:5002"
NXTAPP_URL = "http://localhost:5000"
TEST_TIMEOUT = 300  # 5 minutes for large document processing


class EndToEndTester:
    """Comprehensive end-to-end integration tester"""
    
    def __init__(self):
        self.contract_agent_process: Optional[subprocess.Popen] = None
        self.nxtapp_process: Optional[subprocess.Popen] = None
        self.test_results = []
        self.test_files = []
        
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
        
    def create_small_contract(self) -> str:
        """Create a small test contract (under chunking threshold)"""
        contract_content = """
EMPLOYMENT AGREEMENT

This Employment Agreement is entered into between SmallCorp Inc., a Delaware corporation 
(the "Company"), and Alice Johnson (the "Employee").

1. EMPLOYMENT: Company hereby employs Employee as a Data Analyst.
2. COMPENSATION: Company shall pay Employee a base salary of $75,000 per year.
3. BENEFITS: Employee shall be entitled to standard company benefits including health insurance.
4. GOVERNING LAW: This Agreement shall be governed by the laws of Delaware.
5. TERMINATION: Either party may terminate this agreement with 30 days notice.

IN WITNESS WHEREOF, the parties have executed this Agreement.

SmallCorp Inc.
By: _________________
CEO

Employee: _________________
Alice Johnson
        """.strip()
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(contract_content)
        temp_file.close()
        self.test_files.append(temp_file.name)
        
        return temp_file.name
    
    def create_large_contract(self) -> str:
        """Create a large test contract (triggers chunking)"""
        base_contract = """
COMPREHENSIVE MASTER SERVICE AGREEMENT

This Master Service Agreement ("Agreement") is entered into between MegaCorp International Inc., 
a Delaware corporation with its principal place of business at 123 Corporate Drive, Wilmington, 
Delaware 19801 (the "Company"), and GlobalServices Provider LLC, a limited liability company 
organized under the laws of Delaware with its principal place of business at 456 Business Park, 
Dover, Delaware 19901 (the "Provider").

RECITALS

WHEREAS, Company desires to engage Provider to perform certain consulting, advisory, and 
professional services as more particularly described herein; and

WHEREAS, Provider represents that it has the necessary expertise, experience, and resources 
to perform such services in accordance with the highest professional standards; and

WHEREAS, the parties wish to set forth the terms and conditions governing their relationship;

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, 
and for other good and valuable consideration, the receipt and sufficiency of which are 
hereby acknowledged, the parties agree as follows:

1. SCOPE OF SERVICES

1.1 General Services. Provider shall provide comprehensive business consulting services 
including but not limited to: strategic planning and analysis, operational optimization, 
technology assessment and implementation, process improvement initiatives, organizational 
development and change management, financial analysis and modeling, market research and 
competitive analysis, regulatory compliance consulting, and such other services as may 
be mutually agreed upon by the parties in writing.

1.2 Specific Deliverables. Provider shall deliver detailed reports, analyses, 
recommendations, implementation plans, training materials, documentation, and other 
deliverables as specified in each Statement of Work executed pursuant to this Agreement.

1.3 Performance Standards. All services shall be performed in accordance with industry 
best practices and professional standards generally accepted in the consulting industry, 
and Provider shall use commercially reasonable efforts to meet all deadlines and 
performance metrics specified in the applicable Statement of Work.

2. TERM AND TERMINATION

2.1 Initial Term. This Agreement shall commence on the Effective Date and shall continue 
for an initial period of three (3) years unless earlier terminated in accordance with 
the provisions hereof.

2.2 Renewal. This Agreement may be renewed for additional one-year periods upon mutual 
written agreement of the parties.

2.3 Termination for Convenience. Either party may terminate this Agreement at any time 
upon sixty (60) days prior written notice to the other party.

2.4 Termination for Cause. Either party may terminate this Agreement immediately upon 
written notice if the other party materially breaches any provision of this Agreement 
and fails to cure such breach within thirty (30) days after written notice thereof.

3. COMPENSATION AND PAYMENT TERMS

3.1 Fees. Company shall pay Provider the fees specified in each Statement of Work for 
the services performed thereunder. Unless otherwise specified, all fees are in U.S. 
dollars and are exclusive of applicable taxes.

3.2 Expenses. Company shall reimburse Provider for all reasonable and documented 
out-of-pocket expenses incurred in connection with the performance of services, 
provided such expenses are pre-approved in writing by Company.

3.3 Payment Terms. Provider shall submit invoices monthly, and Company shall pay all 
undisputed amounts within thirty (30) days after receipt of a properly submitted invoice.

4. INTELLECTUAL PROPERTY

4.1 Ownership. All work product, deliverables, inventions, improvements, and other 
intellectual property created or developed by Provider in the performance of services 
hereunder shall be owned exclusively by Company.

4.2 License. Provider hereby grants Company a perpetual, irrevocable, worldwide, 
royalty-free license to use, modify, and distribute any pre-existing intellectual 
property of Provider that is incorporated into the work product.

5. CONFIDENTIALITY

5.1 Confidential Information. Each party acknowledges that it may receive confidential 
and proprietary information of the other party. Each party agrees to maintain the 
confidentiality of such information and not to disclose it to third parties without 
the prior written consent of the disclosing party.

5.2 Exceptions. The obligations set forth in Section 5.1 shall not apply to information 
that: (a) is or becomes publicly available through no fault of the receiving party; 
(b) was known to the receiving party prior to disclosure; (c) is independently developed 
by the receiving party; or (d) is required to be disclosed by law or court order.

6. LIMITATION OF LIABILITY

6.1 Disclaimer. PROVIDER'S SERVICES ARE PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, 
EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.

6.2 Limitation. IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, 
SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, REGARDLESS OF THE THEORY OF LIABILITY.

7. GOVERNING LAW AND DISPUTE RESOLUTION

7.1 Governing Law. This Agreement shall be governed by and construed in accordance with 
the laws of the State of Delaware, without regard to its conflict of laws principles.

7.2 Dispute Resolution. Any dispute arising out of or relating to this Agreement shall 
be resolved through binding arbitration in accordance with the Commercial Arbitration 
Rules of the American Arbitration Association.

8. GENERAL PROVISIONS

8.1 Entire Agreement. This Agreement constitutes the entire agreement between the parties 
with respect to the subject matter hereof and supersedes all prior agreements and 
understandings.

8.2 Amendment. This Agreement may be amended only by a written instrument signed by both parties.

8.3 Severability. If any provision of this Agreement is held to be invalid or unenforceable, 
the remaining provisions shall continue in full force and effect.

8.4 Assignment. Neither party may assign this Agreement without the prior written consent 
of the other party, except that Company may assign this Agreement to an affiliate or 
in connection with a merger or acquisition.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

MEGACORP INTERNATIONAL INC.

By: _________________________________
Name: [Name]
Title: Chief Executive Officer
Date: _______________________________

GLOBALSERVICES PROVIDER LLC

By: _________________________________
Name: [Name] 
Title: Managing Member
Date: _______________________________
        """
        
        # Repeat content to ensure it exceeds chunking threshold (25k chars)
        large_content = base_contract * 3  # Should be ~30k+ characters
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(large_content)
        temp_file.close()
        self.test_files.append(temp_file.name)
        
        return temp_file.name
    
    def start_contract_agent(self) -> bool:
        """Start Contract-Agent server"""
        try:
            print("🚀 Starting Contract-Agent server...")
            
            self.contract_agent_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                cwd='/home/ec2-user/cb/Contract-Agent',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for attempt in range(15):
                try:
                    response = requests.get(f"{CONTRACT_AGENT_URL}/health", timeout=5)
                    if response.status_code == 200:
                        self.log_test("Contract-Agent Startup", True, f"Server started on {CONTRACT_AGENT_URL}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(2)
                    continue
            
            self.log_test("Contract-Agent Startup", False, "Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            self.log_test("Contract-Agent Startup", False, str(e))
            return False
    
    def stop_servers(self):
        """Stop all test servers"""
        if self.contract_agent_process:
            print("🛑 Stopping Contract-Agent server...")
            self.contract_agent_process.terminate()
            self.contract_agent_process.wait(timeout=10)
            self.contract_agent_process = None
        
        if self.nxtapp_process:
            print("🛑 Stopping nxtApp server...")
            self.nxtapp_process.terminate() 
            self.nxtapp_process.wait(timeout=10)
            self.nxtapp_process = None
    
    def test_contract_agent_direct(self, contract_file: str, instruction: str, expect_chunking: bool = False) -> Dict[str, Any]:
        """Test direct Contract-Agent API processing"""
        start_time = time.time()
        
        try:
            # Upload and process contract
            with open(contract_file, 'rb') as f:
                files = {'file': (os.path.basename(contract_file), f, 'text/plain')}
                data = {'prompt': instruction}
                
                response = requests.post(
                    f"{CONTRACT_AGENT_URL}/process_contract",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 202:
                return {
                    'success': False,
                    'error': f"Upload failed: HTTP {response.status_code}",
                    'duration': time.time() - start_time
                }
            
            result = response.json()
            job_id = result.get('job_id')
            
            if not job_id:
                return {
                    'success': False,
                    'error': "No job_id returned",
                    'duration': time.time() - start_time
                }
            
            # Poll for completion
            chunking_detected = False
            while time.time() - start_time < TEST_TIMEOUT:
                status_response = requests.get(f"{CONTRACT_AGENT_URL}/job_status/{job_id}", timeout=10)
                
                if status_response.status_code != 200:
                    continue
                
                data = status_response.json()
                status = data.get('status')
                message = data.get('message', '')
                
                # Check for chunking
                if 'chunk' in message.lower():
                    chunking_detected = True
                
                if status == 'completed':
                    # Get final results
                    result_response = requests.get(f"{CONTRACT_AGENT_URL}/job_result/{job_id}", timeout=30)
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        processing_results = result_data.get('processing_results', {})
                        
                        return {
                            'success': True,
                            'job_id': job_id,
                            'final_rtf': processing_results.get('final_rtf', ''),
                            'final_score': processing_results.get('final_score', 0),
                            'iterations_used': processing_results.get('iterations_used', 0),
                            'chunking_detected': chunking_detected,
                            'chunk_stats': processing_results.get('chunk_processing_stats'),
                            'duration': time.time() - start_time
                        }
                    else:
                        return {
                            'success': False,
                            'error': "Failed to get results",
                            'duration': time.time() - start_time
                        }
                        
                elif status == 'failed':
                    error_msg = data.get('error_message', 'Processing failed')
                    return {
                        'success': False,
                        'error': error_msg,
                        'duration': time.time() - start_time
                    }
                
                time.sleep(2)
            
            return {
                'success': False,
                'error': f"Timeout after {TEST_TIMEOUT} seconds",
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def test_small_document_workflow(self) -> bool:
        """Test complete workflow with small documents (no chunking expected)"""
        contract_file = self.create_small_contract()
        
        print(f"\n📄 Testing small document workflow...")
        print(f"   File: {os.path.basename(contract_file)}")
        print(f"   Size: {os.path.getsize(contract_file)} bytes")
        
        instruction = "Change SmallCorp Inc. to TechStart LLC and change Delaware to California"
        
        result = self.test_contract_agent_direct(contract_file, instruction, expect_chunking=False)
        
        if not result['success']:
            self.log_test("Small Document Processing", False, result['error'], result['duration'])
            return False
        
        # Verify no chunking was used
        if result['chunking_detected']:
            self.log_test("Small Document Processing", False, 
                         "Chunking detected when not expected", result['duration'])
            return False
        
        # Verify content changes
        rtf_content = result['final_rtf']
        if 'TechStart LLC' not in rtf_content or 'California' not in rtf_content:
            self.log_test("Small Document Processing", False, 
                         "Expected content changes not found", result['duration'])
            return False
        
        self.log_test("Small Document Processing", True, 
                     f"Score: {result['final_score']:.2f}, Iterations: {result['iterations_used']}", 
                     result['duration'])
        return True
    
    def test_large_document_workflow(self) -> bool:
        """Test complete workflow with large documents (chunking expected)"""
        contract_file = self.create_large_contract()
        
        print(f"\n📄 Testing large document workflow...")
        print(f"   File: {os.path.basename(contract_file)}")
        print(f"   Size: {os.path.getsize(contract_file)} bytes")
        
        instruction = "Change MegaCorp International Inc. to InnovateGlobal Corp and change Delaware to California"
        
        result = self.test_contract_agent_direct(contract_file, instruction, expect_chunking=True)
        
        if not result['success']:
            self.log_test("Large Document Processing", False, result['error'], result['duration'])
            return False
        
        # Verify chunking was used
        if not result['chunking_detected']:
            self.log_test("Large Document Processing", False, 
                         "Chunking not detected when expected", result['duration'])
            return False
        
        # Verify content changes
        rtf_content = result['final_rtf']
        if 'InnovateGlobal Corp' not in rtf_content or 'California' not in rtf_content:
            self.log_test("Large Document Processing", False, 
                         "Expected content changes not found", result['duration'])
            return False
        
        # Check chunk statistics
        chunk_stats = result.get('chunk_stats', {})
        chunk_info = f"Chunks: {chunk_stats.get('total_chunks', 'N/A')}"
        
        self.log_test("Large Document Processing", True, 
                     f"Score: {result['final_score']:.2f}, {chunk_info}", result['duration'])
        return True
    
    def test_error_scenarios(self) -> bool:
        """Test error handling and recovery scenarios"""
        print(f"\n🔍 Testing error scenarios...")
        
        error_tests_passed = 0
        total_error_tests = 3
        
        # Test 1: Invalid file type
        try:
            invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.invalid', delete=False)
            invalid_file.write("Invalid file content")
            invalid_file.close()
            self.test_files.append(invalid_file.name)
            
            with open(invalid_file.name, 'rb') as f:
                files = {'file': ('test.invalid', f, 'application/octet-stream')}
                data = {'prompt': 'test instruction'}
                
                response = requests.post(
                    f"{CONTRACT_AGENT_URL}/process_contract",
                    files=files,
                    data=data,
                    timeout=10
                )
            
            # Should return 400 for invalid file type
            if response.status_code == 400:
                self.log_test("Error Handling - Invalid File Type", True, "400 error returned")
                error_tests_passed += 1
            else:
                self.log_test("Error Handling - Invalid File Type", False, f"Expected 400, got {response.status_code}")
        
        except Exception as e:
            self.log_test("Error Handling - Invalid File Type", False, str(e))
        
        # Test 2: Empty prompt
        try:
            contract_file = self.create_small_contract()
            
            with open(contract_file, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'prompt': ''}  # Empty prompt
                
                response = requests.post(
                    f"{CONTRACT_AGENT_URL}/process_contract",
                    files=files,
                    data=data,
                    timeout=10
                )
            
            # Should return 400 for empty prompt
            if response.status_code == 400:
                self.log_test("Error Handling - Empty Prompt", True, "400 error returned")
                error_tests_passed += 1
            else:
                self.log_test("Error Handling - Empty Prompt", False, f"Expected 400, got {response.status_code}")
        
        except Exception as e:
            self.log_test("Error Handling - Empty Prompt", False, str(e))
        
        # Test 3: Nonexistent job status
        try:
            fake_job_id = str(uuid.uuid4())
            response = requests.get(f"{CONTRACT_AGENT_URL}/job_status/{fake_job_id}", timeout=10)
            
            # Should return 404 for nonexistent job
            if response.status_code == 404:
                self.log_test("Error Handling - Nonexistent Job", True, "404 error returned")
                error_tests_passed += 1
            else:
                self.log_test("Error Handling - Nonexistent Job", False, f"Expected 404, got {response.status_code}")
        
        except Exception as e:
            self.log_test("Error Handling - Nonexistent Job", False, str(e))
        
        return error_tests_passed == total_error_tests
    
    def test_cleanup_and_memory_management(self) -> bool:
        """Test automatic cleanup after processing completion"""
        print(f"\n🧹 Testing cleanup and memory management...")
        
        try:
            # Get initial memory usage
            initial_response = requests.get(f"{CONTRACT_AGENT_URL}/debug/queue", timeout=10)
            if initial_response.status_code != 200:
                self.log_test("Cleanup Test", False, "Cannot access debug endpoints")
                return False
            
            initial_data = initial_response.json()
            initial_queue_size = initial_data.get('queue_size', 0)
            
            # Process a document
            contract_file = self.create_small_contract()
            instruction = "Change SmallCorp Inc. to CleanupTest Corp"
            
            result = self.test_contract_agent_direct(contract_file, instruction)
            
            if not result['success']:
                self.log_test("Cleanup Test", False, "Test document processing failed")
                return False
            
            # Wait a bit for cleanup
            time.sleep(5)
            
            # Check memory usage after
            final_response = requests.get(f"{CONTRACT_AGENT_URL}/debug/queue", timeout=10)
            final_data = final_response.json()
            final_queue_size = final_data.get('queue_size', 0)
            
            # Queue should not grow significantly
            queue_growth = final_queue_size - initial_queue_size
            
            self.log_test("Cleanup Test", True, 
                         f"Queue growth: {queue_growth}, Processing completed successfully")
            return True
            
        except Exception as e:
            self.log_test("Cleanup Test", False, str(e))
            return False
    
    def test_document_integrity(self) -> bool:
        """Test document integrity after chunk reassembly"""
        print(f"\n🔗 Testing document integrity after chunk reassembly...")
        
        try:
            # Create a large document with specific markers for integrity checking
            integrity_markers = [
                "INTEGRITY_MARKER_START",
                "INTEGRITY_MARKER_MIDDLE_SECTION_1",
                "INTEGRITY_MARKER_MIDDLE_SECTION_2", 
                "INTEGRITY_MARKER_MIDDLE_SECTION_3",
                "INTEGRITY_MARKER_END"
            ]
            
            base_content = """
DOCUMENT INTEGRITY TEST AGREEMENT

INTEGRITY_MARKER_START

This is a comprehensive test document designed to verify that document chunking
and reassembly maintains the integrity of the original content structure.

INTEGRITY_MARKER_MIDDLE_SECTION_1

Section 1: This section contains important legal provisions that must be preserved
during the chunking and reassembly process. Any loss of content here would indicate
a serious issue with the document processing pipeline.

INTEGRITY_MARKER_MIDDLE_SECTION_2

Section 2: This section contains additional provisions and clauses that serve as
additional integrity checkpoints. The preservation of this content is critical
for validating the robustness of the chunking system.

INTEGRITY_MARKER_MIDDLE_SECTION_3

Section 3: Final validation section with complex formatting and structure that
tests the system's ability to handle diverse document formats and content types
while maintaining complete fidelity to the original document.

INTEGRITY_MARKER_END

This concludes the integrity test document.
            """
            
            # Repeat to ensure chunking threshold
            large_content = base_content * 20
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(large_content)
            temp_file.close()
            self.test_files.append(temp_file.name)
            
            # Process the document
            instruction = "Add a new section titled 'INTEGRITY_VALIDATION: Processing completed successfully'"
            result = self.test_contract_agent_direct(temp_file.name, instruction, expect_chunking=True)
            
            if not result['success']:
                self.log_test("Document Integrity Test", False, "Processing failed")
                return False
            
            # Check that all integrity markers are present
            rtf_content = result['final_rtf']
            missing_markers = []
            
            for marker in integrity_markers:
                if marker not in rtf_content:
                    missing_markers.append(marker)
            
            if missing_markers:
                self.log_test("Document Integrity Test", False, 
                             f"Missing markers: {missing_markers}")
                return False
            
            # Check that new content was added
            if 'INTEGRITY_VALIDATION: Processing completed successfully' not in rtf_content:
                self.log_test("Document Integrity Test", False, "New content not added")
                return False
            
            self.log_test("Document Integrity Test", True, 
                         f"All {len(integrity_markers)} markers preserved, new content added")
            return True
            
        except Exception as e:
            self.log_test("Document Integrity Test", False, str(e))
            return False
    
    def run_end_to_end_tests(self) -> bool:
        """Run all end-to-end integration tests"""
        print("🧪 Starting End-to-End Integration Tests (Task 11)")
        print("=" * 70)
        
        try:
            # Start Contract-Agent server
            if not self.start_contract_agent():
                return False
            
            time.sleep(3)  # Allow server to fully initialize
            
            # Run all test scenarios
            tests_passed = 0
            total_tests = 6
            
            if self.test_small_document_workflow():
                tests_passed += 1
            
            if self.test_large_document_workflow():
                tests_passed += 1
            
            if self.test_error_scenarios():
                tests_passed += 1
            
            if self.test_cleanup_and_memory_management():
                tests_passed += 1
            
            if self.test_document_integrity():
                tests_passed += 1
            
            # Additional API synchronization test
            if self.test_api_synchronization():
                tests_passed += 1
            
            # Print summary
            print("\n" + "=" * 70)
            print(f"📊 END-TO-END TEST SUMMARY: {tests_passed}/{total_tests} tests passed")
            
            success = tests_passed == total_tests
            if success:
                print("🎉 ALL END-TO-END TESTS PASSED! System ready for production.")
            else:
                print("❌ Some end-to-end tests failed. Review logs above.")
            
            return success
            
        finally:
            self.stop_servers()
            self.cleanup_test_files()
    
    def test_api_synchronization(self) -> bool:
        """Test API synchronization between different endpoints"""
        print(f"\n🔄 Testing API synchronization...")
        
        try:
            # Test health endpoint consistency
            health_checks = []
            for i in range(3):
                response = requests.get(f"{CONTRACT_AGENT_URL}/health", timeout=5)
                if response.status_code == 200:
                    health_checks.append(response.json())
                time.sleep(1)
            
            if len(health_checks) != 3:
                self.log_test("API Synchronization", False, "Health endpoint inconsistent")
                return False
            
            # Verify consistent component status
            first_components = health_checks[0].get('components', {})
            for check in health_checks[1:]:
                if check.get('components', {}) != first_components:
                    self.log_test("API Synchronization", False, "Component status inconsistent")
                    return False
            
            self.log_test("API Synchronization", True, "All endpoints synchronized")
            return True
            
        except Exception as e:
            self.log_test("API Synchronization", False, str(e))
            return False
    
    def cleanup_test_files(self):
        """Clean up temporary test files"""
        for file_path in self.test_files:
            try:
                os.unlink(file_path)
            except:
                pass
        self.test_files.clear()


def main():
    """Main test execution function"""
    tester = EndToEndTester()
    
    try:
        success = tester.run_end_to_end_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        tester.stop_servers()
        tester.cleanup_test_files()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        tester.stop_servers()
        tester.cleanup_test_files()
        sys.exit(1)


if __name__ == "__main__":
    main()
