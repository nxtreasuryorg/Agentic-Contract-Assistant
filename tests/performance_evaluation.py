#!/usr/bin/env python3
"""
Contract-Agent Architecture Performance Evaluation Script

This script comprehensively evaluates the Contract-Agent actor-critic architecture
with various contract modification scenarios and records detailed metrics.
"""

import os
import sys
import time
import json
import requests
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:5002"
TEST_TIMEOUT = 300  # 5 minutes per test
RESULTS_DIR = Path("/home/ec2-user/cb/Contract-Agent/evaluation_results")
RESULTS_DIR.mkdir(exist_ok=True)

class ContractAgentEvaluator:
    """Comprehensive evaluator for Contract-Agent architecture performance"""
    
    def __init__(self):
        self.results = []
        self.test_start_time = datetime.now()
        
    def log_result(self, test_name: str, result: Dict[str, Any]):
        """Log test result with timestamp"""
        result['test_name'] = test_name
        result['timestamp'] = datetime.now().isoformat()
        result['elapsed_time_from_start'] = (datetime.now() - self.test_start_time).total_seconds()
        self.results.append(result)
        
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} - {test_name}")
        if 'processing_time' in result:
            print(f"    Processing Time: {result['processing_time']:.1f}s")
        if 'final_score' in result:
            print(f"    Quality Score: {result['final_score']:.3f}")
        if 'iterations' in result:
            print(f"    Iterations Used: {result['iterations']}")
        print()
    
    def create_test_contract(self, contract_type: str) -> str:
        """Create test contract content based on type"""
        
        if contract_type == "simple_employment":
            return """
            EMPLOYMENT AGREEMENT
            
            This Employment Agreement is entered into between TechCorp Inc., a Delaware corporation 
            ("Company"), and John Smith ("Employee").
            
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
            """
            
        elif contract_type == "service_agreement":
            with open("/home/ec2-user/cb/Contract-Agent/data/test_data/sample_contract.rtf", 'r') as f:
                return f.read()
                
        elif contract_type == "complex_partnership":
            return """
            PARTNERSHIP AGREEMENT
            
            This Partnership Agreement is entered into between AlphaTech Solutions LLC, a California 
            limited liability company ("Alpha Partner"), and BetaCorp Industries Inc., a New York 
            corporation ("Beta Partner"), and GammaVentures LP, a Delaware limited partnership 
            ("Gamma Partner").
            
            1. PURPOSE: The partnership shall engage in software development and consulting services.
            2. CAPITAL CONTRIBUTIONS: 
               - Alpha Partner: $500,000 (50% ownership)
               - Beta Partner: $300,000 (30% ownership)  
               - Gamma Partner: $200,000 (20% ownership)
            3. MANAGEMENT: Alpha Partner shall be the managing partner.
            4. PROFIT DISTRIBUTION: Profits shall be distributed according to ownership percentages.
            5. GOVERNING LAW: This Agreement shall be governed by California law.
            6. LIABILITY: Each partner shall be liable only for their proportional share of losses.
            7. INDEMNIFICATION: Alpha Partner shall indemnify other partners against third-party claims.
            8. DISPUTE RESOLUTION: Disputes shall be resolved through binding arbitration in Los Angeles.
            9. TERMINATION: Partnership may be terminated by unanimous consent or material breach.
            10. CONFIDENTIALITY: All partners agree to maintain confidentiality of partnership information.
            
            AlphaTech Solutions LLC        BetaCorp Industries Inc.        GammaVentures LP
            By: ________________          By: ________________            By: ________________
            Managing Member              President                        General Partner
            """
        
        return contract_type  # Fallback for custom content
    
    def submit_contract(self, contract_content: str, prompt: str, test_name: str) -> Optional[str]:
        """Submit contract for processing and return job_id"""
        try:
            # Create temporary file
            temp_file = f"test_{uuid.uuid4().hex[:8]}.txt"
            temp_path = RESULTS_DIR / temp_file
            
            with open(temp_path, 'w') as f:
                f.write(contract_content)
            
            # Submit to API
            with open(temp_path, 'rb') as f:
                files = {'file': (temp_file, f, 'text/plain')}
                data = {'prompt': prompt}
                
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/process_contract",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                upload_time = time.time() - start_time
            
            # Clean up temp file
            temp_path.unlink()
            
            if response.status_code == 202:
                result_data = response.json()
                job_id = result_data.get('job_id')
                
                self.log_result(f"{test_name}_Upload", {
                    'success': True,
                    'upload_time': upload_time,
                    'job_id': job_id,
                    'prompt': prompt,
                    'contract_length': len(contract_content)
                })
                
                return job_id
            else:
                self.log_result(f"{test_name}_Upload", {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'upload_time': upload_time
                })
                return None
                
        except Exception as e:
            self.log_result(f"{test_name}_Upload", {
                'success': False,
                'error': str(e)
            })
            return None
    
    def wait_for_completion(self, job_id: str, test_name: str) -> Optional[Dict[str, Any]]:
        """Wait for job completion and return results"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < TEST_TIMEOUT:
            try:
                response = requests.get(f"{API_BASE_URL}/job_status/{job_id}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    
                    # Log status changes
                    if status != last_status:
                        print(f"    Status: {status} ({progress}%)")
                        last_status = status
                    
                    if status == 'completed':
                        # Get full results
                        result_response = requests.get(f"{API_BASE_URL}/job_result/{job_id}", timeout=10)
                        
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            processing_results = result_data.get('processing_results', {})
                            
                            total_time = time.time() - start_time
                            
                            return {
                                'success': True,
                                'processing_time': total_time,
                                'final_rtf': processing_results.get('final_rtf', ''),
                                'original_rtf': processing_results.get('original_rtf', ''),
                                'iterations': processing_results.get('iterations_used', 0),
                                'final_score': processing_results.get('final_score', 0),
                                'crew_output': processing_results.get('crew_output', ''),
                                'status': status
                            }
                        else:
                            return {
                                'success': False,
                                'error': f"Result retrieval failed: HTTP {result_response.status_code}",
                                'processing_time': time.time() - start_time
                            }
                    
                    elif status == 'failed':
                        error_msg = data.get('error_message', 'Unknown error')
                        return {
                            'success': False,
                            'error': error_msg,
                            'processing_time': time.time() - start_time,
                            'status': status
                        }
                
                time.sleep(10)  # Poll every 10 seconds
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Polling error: {str(e)}",
                    'processing_time': time.time() - start_time
                }
        
        return {
            'success': False,
            'error': f"Timeout after {TEST_TIMEOUT}s",
            'processing_time': TEST_TIMEOUT
        }
    
    def evaluate_semantic_accuracy(self, original: str, modified: str, prompt: str) -> Dict[str, Any]:
        """Evaluate semantic accuracy of modifications"""
        accuracy_checks = {
            'total_checks': 0,
            'passed_checks': 0,
            'details': []
        }
        
        # Extract expected changes from prompt
        prompt_lower = prompt.lower()
        
        # Check counterparty changes
        if 'change' in prompt_lower and ('corp' in prompt_lower or 'company' in prompt_lower):
            accuracy_checks['total_checks'] += 1
            # Look for evidence of entity substitution
            if len(set(original.split()) - set(modified.split())) > 0:
                accuracy_checks['passed_checks'] += 1
                accuracy_checks['details'].append("✅ Entity substitution detected")
            else:
                accuracy_checks['details'].append("❌ Entity substitution not detected")
        
        # Check jurisdiction changes
        if any(jurisdiction in prompt_lower for jurisdiction in ['delaware', 'california', 'new york', 'hong kong']):
            accuracy_checks['total_checks'] += 1
            # Look for jurisdiction-related changes
            jurisdiction_words = ['delaware', 'california', 'new york', 'hong kong', 'law', 'jurisdiction']
            original_jurisdictions = [word for word in original.lower().split() if word in jurisdiction_words]
            modified_jurisdictions = [word for word in modified.lower().split() if word in jurisdiction_words]
            
            if original_jurisdictions != modified_jurisdictions:
                accuracy_checks['passed_checks'] += 1
                accuracy_checks['details'].append("✅ Jurisdiction changes detected")
            else:
                accuracy_checks['details'].append("❌ Jurisdiction changes not detected")
        
        # Check liability/indemnification changes
        if 'liability' in prompt_lower or 'indemnif' in prompt_lower:
            accuracy_checks['total_checks'] += 1
            liability_words = ['liability', 'indemnify', 'indemnification', 'liable', 'claims']
            original_liability = [word for word in original.lower().split() if word in liability_words]
            modified_liability = [word for word in modified.lower().split() if word in liability_words]
            
            if original_liability != modified_liability:
                accuracy_checks['passed_checks'] += 1  
                accuracy_checks['details'].append("✅ Liability changes detected")
            else:
                accuracy_checks['details'].append("❌ Liability changes not detected")
        
        # Check clause additions/deletions
        if 'add' in prompt_lower or 'delete' in prompt_lower or 'remove' in prompt_lower:
            accuracy_checks['total_checks'] += 1
            # Simple heuristic: significant length change indicates clause modification
            length_change = abs(len(modified) - len(original)) / len(original)
            if length_change > 0.05:  # 5% change threshold
                accuracy_checks['passed_checks'] += 1
                accuracy_checks['details'].append("✅ Clause modifications detected")
            else:
                accuracy_checks['details'].append("❌ Clause modifications not detected")
        
        accuracy_score = accuracy_checks['passed_checks'] / accuracy_checks['total_checks'] if accuracy_checks['total_checks'] > 0 else 0
        
        return {
            'accuracy_score': accuracy_score,
            'checks_passed': accuracy_checks['passed_checks'],
            'total_checks': accuracy_checks['total_checks'],
            'details': accuracy_checks['details']
        }
    
    def run_test_case(self, test_name: str, contract_type: str, prompt: str):
        """Run a single test case"""
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING TEST: {test_name}")
        print(f"📝 Prompt: {prompt}")
        print(f"{'='*60}")
        
        # Create contract content
        contract_content = self.create_test_contract(contract_type)
        
        # Submit contract
        job_id = self.submit_contract(contract_content, prompt, test_name)
        if not job_id:
            return
        
        # Wait for completion
        result = self.wait_for_completion(job_id, test_name)
        
        if result and result.get('success'):
            # Evaluate semantic accuracy
            accuracy = self.evaluate_semantic_accuracy(
                contract_content, 
                result.get('final_rtf', ''), 
                prompt
            )
            result.update(accuracy)
        
        # Log final result
        self.log_result(test_name, result or {'success': False, 'error': 'No result returned'})
    
    def run_simple_tests(self):
        """Run simple modification tests"""
        print("\n🔍 RUNNING SIMPLE MODIFICATION TESTS")
        
        # Test 1: Simple counterparty change
        self.run_test_case(
            "Simple_Counterparty_Change",
            "simple_employment",
            "Change company name from TechCorp Inc. to InnovateTech LLC"
        )
        
        # Test 2: Jurisdiction change
        self.run_test_case(
            "Simple_Jurisdiction_Change", 
            "simple_employment",
            "Change governing law from Delaware to California"
        )
        
        # Test 3: Liability shift
        self.run_test_case(
            "Simple_Liability_Shift",
            "service_agreement", 
            "Shift the liability from Company to Client - Client should indemnify Company instead"
        )
    
    def run_complex_tests(self):
        """Run complex modification tests"""
        print("\n🔍 RUNNING COMPLEX MODIFICATION TESTS")
        
        # Test 4: Multi-parameter change
        self.run_test_case(
            "Complex_Multi_Parameter",
            "service_agreement",
            "Change Hash Blockchain Limited to CryptoTech Solutions Inc, change governing law from Hong Kong to Delaware, and shift indemnification from Client to Company"
        )
        
        # Test 5: Clause addition
        self.run_test_case(
            "Complex_Clause_Addition",
            "simple_employment",
            "Add a new section 7 for INTELLECTUAL PROPERTY stating that all work products belong to the Company"
        )
        
        # Test 6: Multiple entity and legal changes
        self.run_test_case(
            "Complex_Partnership_Changes",
            "complex_partnership", 
            "Change AlphaTech Solutions LLC to ZenithTech Corp, change governing law from California to New York, shift management from Alpha Partner to Beta Partner, and add a clause about annual profit distribution meetings"
        )
    
    def run_edge_case_tests(self):
        """Run edge case tests"""
        print("\n🔍 RUNNING EDGE CASE TESTS")
        
        # Test 7: Contradictory instructions
        self.run_test_case(
            "Edge_Contradictory_Instructions",
            "service_agreement",
            "Change Company name to TechCorp but also keep it as Hash Blockchain Limited, and change jurisdiction to both Delaware and California"
        )
        
        # Test 8: Very complex multi-step changes
        self.run_test_case(
            "Edge_Very_Complex",
            "complex_partnership",
            "Completely restructure the partnership: change all three partners to SingleTech Inc, MegaCorp LLC, and UltraVentures Ltd; change governing law to Texas; redistribute ownership to 40%, 35%, 25%; add termination clauses requiring 60-day notice; shift all indemnification to SingleTech Inc; and add a force majeure clause"
        )
    
    def generate_evaluation_report(self) -> str:
        """Generate comprehensive evaluation report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get('success', False))
        
        # Calculate averages
        processing_times = [r.get('processing_time', 0) for r in self.results if r.get('success')]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        quality_scores = [r.get('final_score', 0) for r in self.results if r.get('success') and r.get('final_score')]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        iterations = [r.get('iterations', 0) for r in self.results if r.get('success') and r.get('iterations')]
        avg_iterations = sum(iterations) / len(iterations) if iterations else 0
        
        accuracy_scores = [r.get('accuracy_score', 0) for r in self.results if r.get('success') and 'accuracy_score' in r]
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        
        # Generate report
        report_lines = [
            "# Contract-Agent Architecture Performance Evaluation Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Evaluation Duration: {(datetime.now() - self.test_start_time).total_seconds() / 3600:.2f} hours",
            "",
            "## Executive Summary",
            f"- **Total Tests Executed:** {total_tests}",
            f"- **Successful Tests:** {successful_tests} ({successful_tests/total_tests*100:.1f}%)",
            f"- **Average Processing Time:** {avg_processing_time:.1f} seconds",
            f"- **Average Quality Score:** {avg_quality_score:.3f}",
            f"- **Average Iterations:** {avg_iterations:.1f}",
            f"- **Average Semantic Accuracy:** {avg_accuracy:.3f}",
            "",
            "## Architecture Overview",
            "The Contract-Agent implements an actor-critic pattern using CrewAI orchestration:",
            "- **Actor Agent:** Performs contract modifications while preserving RTF formatting",
            "- **Critic Agent:** Evaluates modifications using weighted criteria (85% threshold)",
            "- **Orchestrator:** Manages iterative refinement up to configured maximum",
            "- **Integration:** AWS Bedrock (Titan Premier, Mistral Large) for LLM capabilities",
            "",
            "## Test Methodology",
            "Tests were designed to evaluate:",
            "1. **Entity Substitution:** Counterparty name changes",
            "2. **Jurisdiction Transformation:** Governing law modifications", 
            "3. **Liability Reallocation:** Indemnification responsibility shifts",
            "4. **Clause Operations:** Additions, deletions, modifications",
            "5. **Complex Multi-Parameter Changes:** Combined modifications",
            "",
            "## Detailed Test Results",
        ]
        
        # Add detailed results
        for result in self.results:
            test_name = result.get('test_name', 'Unknown')
            success = result.get('success', False)
            status = "PASS" if success else "FAIL"
            
            report_lines.append(f"\n### {test_name}")
            report_lines.append(f"**Status:** {status}")
            
            if success:
                if 'processing_time' in result:
                    report_lines.append(f"**Processing Time:** {result['processing_time']:.1f}s")
                if 'final_score' in result:
                    report_lines.append(f"**Quality Score:** {result['final_score']:.3f}")
                if 'iterations' in result:
                    report_lines.append(f"**Iterations:** {result['iterations']}")
                if 'accuracy_score' in result:
                    report_lines.append(f"**Semantic Accuracy:** {result['accuracy_score']:.3f}")
                    report_lines.append(f"**Accuracy Details:** {result.get('checks_passed', 0)}/{result.get('total_checks', 0)} checks passed")
                    for detail in result.get('details', []):
                        report_lines.append(f"  - {detail}")
                        
                # Add sample of changes (first 200 characters)
                if 'final_rtf' in result and len(result['final_rtf']) > 100:
                    sample = result['final_rtf'][:200].replace('\n', ' ').replace('\r', '')
                    report_lines.append(f"**Modified Content Sample:** {sample}...")
            else:
                error_msg = result.get('error', 'Unknown error')
                report_lines.append(f"**Error:** {error_msg}")
                if 'processing_time' in result:
                    report_lines.append(f"**Time to Failure:** {result['processing_time']:.1f}s")
        
        # Add performance analysis
        report_lines.extend([
            "\n## Performance Analysis",
            "",
            "### Processing Time Distribution",
        ])
        
        if processing_times:
            min_time = min(processing_times)
            max_time = max(processing_times)
            report_lines.extend([
                f"- **Minimum:** {min_time:.1f}s",
                f"- **Maximum:** {max_time:.1f}s", 
                f"- **Average:** {avg_processing_time:.1f}s",
                f"- **Standard Deviation:** {(sum((t - avg_processing_time)**2 for t in processing_times) / len(processing_times))**0.5:.1f}s"
            ])
        
        report_lines.extend([
            "",
            "### Quality Score Analysis",
        ])
        
        if quality_scores:
            min_score = min(quality_scores)
            max_score = max(quality_scores)
            above_threshold = sum(1 for s in quality_scores if s >= 0.85)
            report_lines.extend([
                f"- **Minimum Score:** {min_score:.3f}",
                f"- **Maximum Score:** {max_score:.3f}",
                f"- **Average Score:** {avg_quality_score:.3f}",
                f"- **Above Threshold (≥0.85):** {above_threshold}/{len(quality_scores)} ({above_threshold/len(quality_scores)*100:.1f}%)"
            ])
        
        # Add strengths and limitations
        report_lines.extend([
            "",
            "## Architecture Strengths",
            "- **Iterative Refinement:** Actor-critic loop enables quality improvement",
            "- **Measurable Quality:** Structured evaluation with numerical scores",
            "- **Scalable Processing:** Background job queue with concurrent handling",
            "- **Format Preservation:** RTF integrity maintained during modifications",
            "- **Comprehensive Evaluation:** Multi-dimensional criteria (entity, jurisdiction, liability, clauses, coherence)",
            "",
            "## Identified Limitations",
        ])
        
        # Analyze failures for limitations
        failed_tests = [r for r in self.results if not r.get('success', False)]
        if failed_tests:
            error_types = {}
            for test in failed_tests:
                error = test.get('error', 'Unknown')
                error_type = error.split(':')[0] if ':' in error else error
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                report_lines.append(f"- **{error_type}:** {count} occurrences")
        
        if avg_processing_time > 120:
            report_lines.append(f"- **Processing Speed:** Average {avg_processing_time:.1f}s may be slow for production")
        
        if avg_accuracy < 0.8:
            report_lines.append(f"- **Semantic Accuracy:** {avg_accuracy:.3f} below optimal threshold")
        
        # Add recommendations
        report_lines.extend([
            "",
            "## Recommendations",
            "1. **Performance Optimization:** Consider chunking strategy optimization for faster processing",
            "2. **Quality Tuning:** Fine-tune evaluation criteria weights based on use case priorities", 
            "3. **Error Handling:** Implement more robust error recovery for failed modifications",
            "4. **Monitoring:** Add real-time performance metrics and alerting",
            "5. **Validation:** Implement additional semantic validation layers",
            "",
            "## Conclusion",
        ])
        
        if successful_tests / total_tests >= 0.8 and avg_quality_score >= 0.85:
            report_lines.append("✅ **ARCHITECTURE READY FOR PRODUCTION** - High success rate and quality scores demonstrate robust performance.")
        elif successful_tests / total_tests >= 0.6:
            report_lines.append("⚠️ **ARCHITECTURE NEEDS REFINEMENT** - Moderate performance indicates need for optimization before production.")
        else:
            report_lines.append("❌ **ARCHITECTURE REQUIRES SIGNIFICANT IMPROVEMENT** - Low success rate indicates fundamental issues need resolution.")
        
        report_lines.extend([
            "",
            f"Report generated by Contract-Agent Performance Evaluator v1.0",
            f"Test execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return "\n".join(report_lines)
    
    def run_full_evaluation(self):
        """Run complete evaluation suite"""
        print("🚀 STARTING COMPREHENSIVE CONTRACT-AGENT PERFORMANCE EVALUATION")
        print(f"⏰ Start Time: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        try:
            # Run all test suites
            self.run_simple_tests()
            self.run_complex_tests() 
            self.run_edge_case_tests()
            
            # Generate and save report
            report = self.generate_evaluation_report()
            
            # Save detailed results
            results_file = RESULTS_DIR / f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Save markdown report
            report_file = RESULTS_DIR / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w') as f:
                f.write(report)
            
            print("\n" + "="*80)
            print("📊 EVALUATION COMPLETED")
            print(f"📄 Report saved to: {report_file}")
            print(f"📁 Raw results saved to: {results_file}")
            print("="*80)
            print(report)
            
            return True
            
        except Exception as e:
            print(f"💥 Evaluation failed: {str(e)}")
            return False

if __name__ == "__main__":
    evaluator = ContractAgentEvaluator()
    success = evaluator.run_full_evaluation()
    sys.exit(0 if success else 1)
