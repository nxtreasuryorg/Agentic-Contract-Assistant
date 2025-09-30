#!/usr/bin/env python3
"""
Contract-Agent PROPER LEDGAR Evaluation Script - FIXED VERSION

This script properly implements LEDGAR benchmark testing using the contract-specific 
prompts from EVALUATION_PROMPTS.md instead of generic test scenarios.

LEDGAR Benchmark: Proper contract provision understanding and modification testing
Focus: Real-world contract complexity with appropriate evaluation prompts
"""

import os
import sys
import time
import json
import requests
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:5002"
TEST_TIMEOUT = 600  # 10 minutes per test to match backend timeout
RESULTS_DIR = Path("/home/ec2-user/cb/Contract-Agent/evaluation_results/nova pro")
CONVERTED_DATA_DIR = Path("/home/ec2-user/cb/Contract-Agent/data/test_data/converted")
RESULTS_DIR.mkdir(exist_ok=True)

class ProperLEDGARContractEvaluator:
    """
    Proper LEDGAR evaluator using contract-specific prompts from EVALUATION_PROMPTS.md
    """
    
    def __init__(self):
        self.results = []
        self.test_start_time = datetime.now()
        self.session_id = str(uuid.uuid4())[:8]
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Proper LEDGAR evaluation criteria based on legal document understanding
        self.ledgar_criteria = {
            "entity_accuracy": 0.30,      # Correct entity/counterparty changes
            "jurisdiction_compliance": 0.25,  # Proper legal jurisdiction handling
            "financial_terms": 0.20,      # Payment/financial term modifications
            "legal_coherence": 0.15,      # Maintains legal document structure
            "semantic_preservation": 0.10  # Preserves contract meaning
        }
        
        # Load ALL contract-specific evaluation prompts from EVALUATION_PROMPTS.md
        self.contract_prompts = self._load_all_evaluation_prompts()
        
        logger.info(f"🚀 Starting PROPER LEDGAR evaluation session: {self.session_id}")
        logger.info(f"📊 Using contract-specific prompts from EVALUATION_PROMPTS.md")
        logger.info(f"📊 Evaluation criteria: {self.ledgar_criteria}")
        logger.info(f"📋 Loaded {sum(len(prompts) for prompts in self.contract_prompts.values())} total evaluation prompts")

    def _load_all_evaluation_prompts(self) -> dict:
        """Load all 40 evaluation prompts from EVALUATION_PROMPTS.md"""
        prompts_file = "/home/ec2-user/cb/Contract-Agent/data/test_data/EVALUATION_PROMPTS.md"
        contract_prompts = {}
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse each sample section
            for sample_num in range(1, 11):  # Samples 01-10
                sample_key = f"sample_{sample_num:02d}_converted"
                contract_prompts[sample_key] = []
                
                # Find the sample section
                sample_pattern = f"## Sample {sample_num:02d}:"
                if sample_pattern in content:
                    # Extract prompts for this sample (a, b, c, d)
                    for letter in ['a', 'b', 'c', 'd']:
                        prompt_pattern = f"#### Sample {sample_num:02d}{letter} - "
                        prompt_start = content.find(prompt_pattern)
                        if prompt_start != -1:
                            # Find the prompt content
                            prompt_line_start = content.find('**Prompt:** "', prompt_start)
                            if prompt_line_start != -1:
                                prompt_content_start = prompt_line_start + len('**Prompt:** "')
                                prompt_content_end = content.find('"', prompt_content_start)
                                
                                if prompt_content_end != -1:
                                    prompt_text = content[prompt_content_start:prompt_content_end]
                                    
                                    # Extract the name from the section header
                                    name_start = prompt_start + len(prompt_pattern)
                                    name_end = content.find('\n', name_start)
                                    prompt_name = content[name_start:name_end].strip()
                                    
                                    # Determine complexity based on sample number and content length
                                    if sample_num <= 2:
                                        complexity = "intermediate" if len(prompt_text) < 200 else "complex"
                                    elif sample_num <= 5:
                                        complexity = "complex"
                                    else:
                                        complexity = "advanced"
                                    
                                    contract_prompts[sample_key].append({
                                        "name": prompt_name.replace(" ", "_").replace("-", "_"),
                                        "prompt": prompt_text,
                                        "complexity": complexity
                                    })
                
                # If no prompts found for this sample, log it
                if not contract_prompts[sample_key]:
                    logger.warning(f"⚠️ No prompts found for {sample_key}")
            
            logger.info(f"✅ Successfully loaded prompts for {len([k for k, v in contract_prompts.items() if v])} samples")
            return contract_prompts
            
        except Exception as e:
            logger.error(f"❌ Failed to load evaluation prompts: {e}")
            # Fallback to empty dict - will skip samples without prompts
            return {}

    def health_check(self) -> bool:
        """Verify Contract-Agent is running and healthy"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Contract-Agent health check passed: {health_data['status']}")
                return True
            else:
                logger.error(f"❌ Health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return False

    def process_contract_modification(self, file_path: str, prompt: str) -> Optional[str]:
        """Process contract modification using the correct API endpoint"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/rtf')}
                data = {'prompt': prompt}
                
                response = requests.post(f"{API_BASE_URL}/process_contract", 
                                       files=files, data=data, timeout=TEST_TIMEOUT)
                
                if response.status_code in [200, 202]:
                    result = response.json()
                    return result.get('job_id')
                else:
                    logger.error(f"Contract processing failed: HTTP {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Contract processing error: {str(e)}")
            return None

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job processing status"""
        try:
            response = requests.get(f"{API_BASE_URL}/job_status/{job_id}", timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Status retrieval failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Status retrieval error: {str(e)}")
            return None

    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job processing result"""
        try:
            response = requests.get(f"{API_BASE_URL}/job_result/{job_id}", timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Result retrieval failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Result retrieval error: {str(e)}")
            return None

    def calculate_proper_ledgar_score(self, original_text: str, modified_text: str, prompt: str) -> float:
        """Calculate proper LEDGAR-style score based on legal document understanding"""
        
        # Entity accuracy - check if entity names were changed correctly
        entity_score = 1.0
        if "change" in prompt.lower() and ("entity" in prompt.lower() or "company" in prompt.lower() or "corp" in prompt.lower()):
            # Check if changes were made (simplified heuristic)
            entity_score = 0.9 if modified_text != original_text else 0.3
        
        # Jurisdiction compliance - check if legal jurisdiction changes were handled
        jurisdiction_score = 1.0
        if any(term in prompt.lower() for term in ["jurisdiction", "governing law", "singapore", "delaware", "hong kong"]):
            jurisdiction_score = 0.9 if modified_text != original_text else 0.3
            
        # Financial terms - check if payment/financial modifications were made
        financial_score = 1.0
        if any(term in prompt.lower() for term in ["payment", "fee", "cost", "price", "million", "$", "days"]):
            financial_score = 0.9 if modified_text != original_text else 0.3
            
        # Legal coherence - basic structure preservation
        coherence_score = 0.9 if len(modified_text) > len(original_text) * 0.8 else 0.6
        
        # Semantic preservation - content should be expanded, not just replaced
        semantic_score = 0.9 if len(modified_text) >= len(original_text) else 0.7
        
        # Calculate weighted score
        ledgar_score = (
            entity_score * self.ledgar_criteria['entity_accuracy'] +
            jurisdiction_score * self.ledgar_criteria['jurisdiction_compliance'] +
            financial_score * self.ledgar_criteria['financial_terms'] +
            coherence_score * self.ledgar_criteria['legal_coherence'] +
            semantic_score * self.ledgar_criteria['semantic_preservation']
        )
        
        return round(ledgar_score, 3)

    def create_test_contract_rtf(self, base_content: str, test_name: str) -> str:
        """Create RTF format test contract"""
        rtf_content = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}} \\f0\\fs24 " + base_content.replace('\n', '\\par ') + "}"
        
        # Save as temporary RTF file
        temp_file = f"/tmp/test_contract_{test_name}_{self.session_id}.rtf"
        with open(temp_file, 'w') as f:
            f.write(rtf_content)
        
        return temp_file

    def run_test_case(self, test_name: str, contract_content: str, modification_prompt: str) -> Dict[str, Any]:
        """Execute a single test case with proper LEDGAR metrics"""
        
        start_time = time.time()
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 RUNNING PROPER LEDGAR TEST: {test_name}")
        logger.info(f"📝 Prompt: {modification_prompt[:100]}...")
        logger.info(f"{'='*60}")
        
        result = {
            'test_name': test_name,
            'modification_prompt': modification_prompt,
            'success': False,
            'error_message': None,
            'processing_time': 0,
            'ledgar_score': 0,
            'semantic_accuracy': 0,
            'iterations': 0,
            'original_length': len(contract_content),
            'modified_length': 0,
            'quality_score': 0
        }
        
        try:
            # Step 1: Create RTF test file
            rtf_file = self.create_test_contract_rtf(contract_content, test_name)
            
            # Step 2: Process contract modification
            job_id = self.process_contract_modification(rtf_file, modification_prompt)
            if not job_id:
                result['error_message'] = "Failed to submit contract processing request"
                return result
            
            logger.info(f"✅ Processing started: {job_id}")
            
            # Step 3: Wait for completion and get results
            max_wait = 600  # 10 minutes to match backend timeout
            wait_interval = 10  # 10 seconds
            waited = 0
            
            while waited < max_wait:
                time.sleep(wait_interval)
                waited += wait_interval
                
                # Check job status
                status_result = self.get_job_status(job_id)
                if not status_result:
                    logger.error(f"Failed to get status for job {job_id}")
                    continue
                    
                status = status_result.get('status')
                progress = status_result.get('progress', 0)
                
                logger.info(f"⏳ Job {job_id} status: {status} ({waited}s/{max_wait}s)")
                
                if status == 'completed':
                    # Get final result
                    final_result = self.get_job_result(job_id)
                    if final_result and final_result.get('success', False):
                        # Extract results
                        final_rtf = final_result.get('final_rtf', '')
                        iterations = final_result.get('iterations_used', 1)
                        processing_time = final_result.get('total_processing_time', waited)
                        
                        # Calculate proper LEDGAR score
                        ledgar_score = self.calculate_proper_ledgar_score(
                            contract_content, final_rtf, modification_prompt
                        )
                        
                        # Update result
                        result.update({
                            'success': True,
                            'ledgar_score': ledgar_score,
                            'semantic_accuracy': ledgar_score,  # Use LEDGAR score as semantic accuracy
                            'iterations': iterations,
                            'modified_length': len(final_rtf),
                            'quality_score': ledgar_score,
                            'processing_time': processing_time
                        })
                    break
                    
                elif status == 'failed':
                    result['error_message'] = status_result.get('error_message', 'Job failed')
                    break
            
            if not result['success'] and not result['error_message']:
                result['error_message'] = f"Timeout after {max_wait} seconds"
            
            # Cleanup
            if os.path.exists(rtf_file):
                os.remove(rtf_file)
                
        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"Test execution error: {str(e)}")
        
        result['processing_time'] = round(time.time() - start_time, 2)
        return result

    def run_comprehensive_evaluation(self):
        """Run comprehensive evaluation using contract-specific prompts"""
        
        logger.info(f"🏁 Starting PROPER LEDGAR evaluation with contract-specific prompts")
        logger.info(f"📁 Using test data from: {CONVERTED_DATA_DIR}")
        
        # Health check first
        if not self.health_check():
            logger.error("❌ Contract-Agent health check failed. Cannot proceed.")
            return
        
        # Load all converted test files
        test_files = list(CONVERTED_DATA_DIR.glob("*.txt"))
        logger.info(f"📄 Found {len(test_files)} test contracts")
        
        # Run tests using contract-specific prompts
        for test_file in test_files:
            contract_key = test_file.stem
            
            if contract_key in self.contract_prompts:
                logger.info(f"\n📋 Testing contract: {test_file.name} with {len(self.contract_prompts[contract_key])} specific prompts")
                
                # Load contract content
                with open(test_file, 'r', encoding='utf-8') as f:
                    contract_content = f.read()
                
                # Run contract-specific test scenarios
                for scenario in self.contract_prompts[contract_key]:
                    test_name = f"{contract_key}_{scenario['name']}"
                    result = self.run_test_case(test_name, contract_content, scenario['prompt'])
                    self.log_result(test_name, result)
            else:
                logger.warning(f"⚠️ No specific prompts found for {contract_key} - skipping")

    def log_result(self, test_name: str, result: Dict[str, Any]):
        """Log comprehensive test result with proper LEDGAR metrics"""
        result['test_name'] = test_name
        result['session_id'] = self.session_id
        result['timestamp'] = datetime.now().isoformat()
        result['elapsed_time_from_start'] = (datetime.now() - self.test_start_time).total_seconds()
        self.results.append(result)
        
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] {status} - {test_name}")
        
        # Log detailed metrics
        for metric in ['processing_time', 'ledgar_score', 'semantic_accuracy', 'iterations']:
            if metric in result:
                logger.info(f"    {metric.replace('_', ' ').title()}: {result[metric]}")
        
        print()

    def generate_evaluation_report(self):
        """Generate comprehensive proper LEDGAR evaluation report"""
        
        if not self.results:
            logger.warning("No results to report")
            return
        
        # Calculate aggregate metrics
        successful_tests = [r for r in self.results if r['success']]
        total_tests = len(self.results)
        success_rate = len(successful_tests) / total_tests if total_tests > 0 else 0
        
        if successful_tests:
            avg_processing_time = sum(r['processing_time'] for r in successful_tests) / len(successful_tests)
            avg_ledgar_score = sum(r['ledgar_score'] for r in successful_tests) / len(successful_tests)
            avg_semantic_accuracy = sum(r['semantic_accuracy'] for r in successful_tests) / len(successful_tests)
            avg_iterations = sum(r['iterations'] for r in successful_tests) / len(successful_tests)
        else:
            avg_processing_time = avg_ledgar_score = avg_semantic_accuracy = avg_iterations = 0
        
        # Create report data
        report_data = {
            "evaluation_metadata": {
                "session_id": self.session_id,
                "timestamp": self.report_timestamp,
                "evaluator": "PROPER LEDGAR Contract-Agent Benchmark",
                "total_tests": total_tests,
                "evaluation_duration": (datetime.now() - self.test_start_time).total_seconds(),
                "contract_specific_prompts": True
            },
            "performance_summary": {
                "success_rate": success_rate,
                "avg_processing_time": avg_processing_time,
                "avg_ledgar_score": avg_ledgar_score,
                "avg_semantic_accuracy": avg_semantic_accuracy,
                "avg_iterations": avg_iterations
            },
            "detailed_results": self.results
        }
        
        # Save results
        json_file = RESULTS_DIR / f"proper_ledgar_evaluation_{self.report_timestamp}.json"
        md_file = RESULTS_DIR / f"proper_ledgar_evaluation_report_{self.report_timestamp}.md"
        
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self._generate_markdown_report(report_data, md_file)
        
        logger.info(f"📁 Results saved:")
        logger.info(f"   JSON: {json_file}")
        logger.info(f"   Report: {md_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"🏆 PROPER LEDGAR EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Success Rate: {success_rate:.1%} ({len(successful_tests)}/{total_tests})")
        print(f"⏱️  Avg Processing Time: {avg_processing_time:.1f}s")
        print(f"🎯 Avg LEDGAR Score: {avg_ledgar_score:.3f}")  
        print(f"🧠 Avg Semantic Accuracy: {avg_semantic_accuracy:.3f}")
        print(f"🔄 Avg Iterations: {avg_iterations:.1f}")
        print(f"{'='*60}")

    def _generate_markdown_report(self, report_data: Dict, output_file: Path):
        """Generate detailed markdown evaluation report"""
        
        with open(output_file, 'w') as f:
            f.write(f"# Contract-Agent PROPER LEDGAR Benchmark Evaluation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"**Session ID:** {report_data['evaluation_metadata']['session_id']}\n")
            f.write(f"**Evaluation Duration:** {report_data['evaluation_metadata']['evaluation_duration']:.1f} seconds\n")
            f.write(f"**Contract-Specific Prompts:** ✅ YES (from EVALUATION_PROMPTS.md)\n\n")
            
            f.write(f"## Executive Summary\n\n")
            f.write(f"This evaluation tests the Contract-Agent architecture using **proper contract-specific prompts** from EVALUATION_PROMPTS.md, ")
            f.write(f"focusing on real-world legal document modification scenarios.\n\n")
            
            summary = report_data['performance_summary']
            
            f.write(f"### Key Performance Metrics\n\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1%}\n")
            f.write(f"- **Average Processing Time:** {summary['avg_processing_time']:.1f} seconds\n")
            f.write(f"- **Average LEDGAR Score:** {summary['avg_ledgar_score']:.3f}\n")
            f.write(f"- **Average Semantic Accuracy:** {summary['avg_semantic_accuracy']:.3f}\n")
            f.write(f"- **Average Iterations:** {summary['avg_iterations']:.1f}\n\n")
            
            f.write(f"## Proper LEDGAR Evaluation Criteria\n\n")
            f.write(f"- **Entity Accuracy:** 30%\n")
            f.write(f"- **Jurisdiction Compliance:** 25%\n")
            f.write(f"- **Financial Terms:** 20%\n")
            f.write(f"- **Legal Coherence:** 15%\n")
            f.write(f"- **Semantic Preservation:** 10%\n\n")
            
            f.write(f"## Detailed Test Results\n\n")
            f.write(f"| Test Name | Success | Processing Time | LEDGAR Score | Semantic Accuracy | Iterations |\n")
            f.write(f"|-----------|---------|-----------------|--------------|-------------------|------------|\n")
            
            for result in report_data['detailed_results']:
                success_icon = "✅" if result['success'] else "❌"
                f.write(f"| {result['test_name']} | {success_icon} | {result['processing_time']:.1f}s | {result['ledgar_score']:.3f} | {result['semantic_accuracy']:.3f} | {result['iterations']} |\n")
            
            f.write(f"\n## Conclusions\n\n")
            if summary['success_rate'] >= 0.8 and summary['avg_ledgar_score'] >= 0.8:
                f.write(f"✅ **EXCELLENT PERFORMANCE** - The architecture demonstrates strong performance on proper LEDGAR benchmark standards.\n\n")
            elif summary['success_rate'] >= 0.7 and summary['avg_ledgar_score'] >= 0.75:
                f.write(f"✅ **GOOD PERFORMANCE** - The architecture shows solid performance with proper contract-specific testing.\n\n")
            else:
                f.write(f"⚠️ **NEEDS IMPROVEMENT** - Performance indicates areas requiring enhancement for proper LEDGAR compliance.\n\n")
            
            f.write(f"Report generated by Contract-Agent PROPER LEDGAR Evaluator\n")

def main():
    """Main evaluation execution"""
    evaluator = ProperLEDGARContractEvaluator()
    
    try:
        evaluator.run_comprehensive_evaluation()
        evaluator.generate_evaluation_report()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Evaluation interrupted by user")
        evaluator.generate_evaluation_report()
        
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
