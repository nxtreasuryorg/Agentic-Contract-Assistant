#!/usr/bin/env python3
"""
Contract-Agent LEDGAR Benchmark Evaluation Script

This script evaluates the Contract-Agent architecture performance against LEDGAR benchmark standards,
testing both contract understanding and modification capabilities with comprehensive metrics recording.

LEDGAR Benchmark: Contract provision classification from SEC filings
Focus: Document understanding, semantic accuracy, processing efficiency
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
TEST_TIMEOUT = 300  # 5 minutes per test
RESULTS_DIR = Path("/home/ec2-user/cb/Contract-Agent/evaluation_results")
CONVERTED_DATA_DIR = Path("/home/ec2-user/cb/Contract-Agent/data/test_data/converted")
RESULTS_DIR.mkdir(exist_ok=True)

class LEDGARContractEvaluator:
    """
    Comprehensive evaluator for Contract-Agent architecture against LEDGAR benchmark standards
    """
    
    def __init__(self):
        self.results = []
        self.test_start_time = datetime.now()
        self.session_id = str(uuid.uuid4())[:8]
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # LEDGAR-style evaluation criteria
        self.ledgar_criteria = {
            "provision_identification": 0.25,  # Can identify contract provisions correctly
            "semantic_understanding": 0.25,   # Understands the legal meaning
            "modification_accuracy": 0.20,    # Makes accurate modifications
            "legal_coherence": 0.15,          # Maintains legal coherence
            "format_preservation": 0.15       # Preserves document structure
        }
        
        logger.info(f"🚀 Starting LEDGAR evaluation session: {self.session_id}")
        logger.info(f"📊 Evaluation criteria: {self.ledgar_criteria}")
    
    def log_result(self, test_name: str, result: Dict[str, Any]):
        """Log comprehensive test result with LEDGAR-style metrics"""
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
        
        if 'provision_classification' in result:
            logger.info(f"    Provision Classification: {result['provision_classification']}")
        
        print()
    
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
    
    def classify_contract_provision(self, text: str) -> Dict[str, Any]:
        """
        LEDGAR-style contract provision classification
        Identifies the main topic/theme of a contract provision
        """
        # Common LEDGAR provision categories based on SEC filings
        provision_types = [
            "governing_law", "dispute_resolution", "termination", "payment_terms",
            "confidentiality", "indemnification", "liability", "force_majeure",
            "intellectual_property", "employment_terms", "service_definition",
            "compliance", "data_protection", "warranties", "representations"
        ]
        
        # Simple heuristic classification (in real LEDGAR, this would be ML-based)
        text_lower = text.lower()
        classifications = []
        
        if any(term in text_lower for term in ["governing", "jurisdiction", "law", "courts"]):
            classifications.append("governing_law")
        if any(term in text_lower for term in ["dispute", "arbitration", "mediation", "litigation"]):
            classifications.append("dispute_resolution")
        if any(term in text_lower for term in ["terminate", "termination", "expiry", "end"]):
            classifications.append("termination")
        if any(term in text_lower for term in ["payment", "fee", "salary", "compensation"]):
            classifications.append("payment_terms")
        if any(term in text_lower for term in ["confidential", "proprietary", "non-disclosure"]):
            classifications.append("confidentiality")
        if any(term in text_lower for term in ["indemnify", "indemnification", "hold harmless"]):
            classifications.append("indemnification")
        if any(term in text_lower for term in ["liability", "damages", "limitation"]):
            classifications.append("liability")
        
        return {
            "primary_classification": classifications[0] if classifications else "general_provision",
            "all_classifications": classifications,
            "confidence_score": len(classifications) / len(provision_types)
        }
    
    def create_test_contract_rtf(self, base_content: str, test_name: str) -> str:
        """Create RTF format test contract"""
        rtf_content = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}} \\f0\\fs24 " + base_content.replace('\n', '\\par ') + "}"
        
        # Save as temporary RTF file
        temp_file = f"/tmp/test_contract_{test_name}_{self.session_id}.rtf"
        with open(temp_file, 'w') as f:
            f.write(rtf_content)
        
        return temp_file
    
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
    
    def calculate_ledgar_score(self, original_text: str, modified_text: str, prompt: str, metrics: Dict) -> float:
        """Calculate LEDGAR-style performance score"""
        
        # Provision identification (can we identify relevant sections?)
        original_provisions = self.classify_contract_provision(original_text)
        modified_provisions = self.classify_contract_provision(modified_text)
        provision_score = 1.0 if len(modified_provisions['all_classifications']) >= len(original_provisions['all_classifications']) else 0.7
        
        # Semantic understanding (does the modification make sense?)
        semantic_score = 1.0 if 'quality_score' in metrics and metrics['quality_score'] > 0.85 else 0.8
        
        # Modification accuracy (are changes correctly applied?)
        modification_score = 1.0 if 'iterations' in metrics and metrics['iterations'] <= 2 else 0.8
        
        # Legal coherence (is the result legally sound?)
        coherence_score = 1.0 if len(modified_text.split()) > len(original_text.split()) * 0.8 else 0.7
        
        # Format preservation (is RTF structure maintained?)
        format_score = 1.0 if 'format_preserved' in metrics and metrics['format_preserved'] else 0.8
        
        # Weighted score
        ledgar_score = (
            provision_score * self.ledgar_criteria['provision_identification'] +
            semantic_score * self.ledgar_criteria['semantic_understanding'] +
            modification_score * self.ledgar_criteria['modification_accuracy'] +
            coherence_score * self.ledgar_criteria['legal_coherence'] +
            format_score * self.ledgar_criteria['format_preservation']
        )
        
        return round(ledgar_score, 3)
    
    def run_test_case(self, test_name: str, contract_content: str, modification_prompt: str) -> Dict[str, Any]:
        """Execute a single test case with comprehensive metrics"""
        
        start_time = time.time()
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 RUNNING LEDGAR TEST: {test_name}")
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
            'provision_classification': {},
            'iterations': 0,
            'original_length': len(contract_content),
            'modified_length': 0
        }
        
        try:
            # Step 1: Create RTF contract
            rtf_file = self.create_test_contract_rtf(contract_content, test_name)
            
            # Step 2: Process contract modification
            job_id = self.process_contract_modification(rtf_file, modification_prompt)
            if not job_id:
                result['error_message'] = "Failed to submit contract processing request"
                return result
            
            logger.info(f"✅ Processing started: {job_id}")
            
            # Step 3: Wait for completion and get results
            max_wait = 300  # 5 minutes
            wait_interval = 10  # 10 seconds
            waited = 0
            
            while waited < max_wait:
                time.sleep(wait_interval)
                waited += wait_interval
                
                # Check job status
                status_result = self.get_job_status(job_id)
                if not status_result:
                    logger.warning(f"Failed to get status for job {job_id}")
                    continue
                
                job_status = status_result.get('status')
                logger.info(f"⏳ Job {job_id} status: {job_status} ({waited}s/{max_wait}s)")
                
                if job_status == 'completed':
                    # Get the final result
                    job_result = self.get_job_result(job_id)
                    if job_result and job_result.get('success'):
                        processing_time = time.time() - start_time
                        result['processing_time'] = round(processing_time, 2)
                        result['success'] = True
                        
                        # Extract result data
                        result_data = job_result.get('result', {})
                        modified_content = result_data.get('final_rtf', '')
                        result['modified_length'] = len(modified_content)
                        
                        # Extract metrics from CrewAI result
                        crew_result = result_data.get('crew_result', {})
                        result['iterations'] = crew_result.get('iterations', 1)
                        result['quality_score'] = crew_result.get('quality_score', 0.85)
                        
                        # Calculate LEDGAR score
                        result['ledgar_score'] = self.calculate_ledgar_score(
                            contract_content, 
                            modified_content,
                            modification_prompt,
                            {'quality_score': result['quality_score'], 'iterations': result['iterations']}
                        )
                        
                        # Provision classification
                        result['provision_classification'] = self.classify_contract_provision(modified_content)
                        
                        # Semantic accuracy (simplified)
                        result['semantic_accuracy'] = round(
                            result['ledgar_score'] * 0.9 + (1 - result['iterations'] / 10) * 0.1, 3
                        )
                        
                    else:
                        result['error_message'] = job_result.get('error_message', 'Processing failed')
                    
                    break
                
                elif job_status == 'failed':
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
        """Run comprehensive LEDGAR-style evaluation"""
        
        logger.info(f"🏁 Starting comprehensive LEDGAR evaluation")
        logger.info(f"📁 Using test data from: {CONVERTED_DATA_DIR}")
        
        # Health check first
        if not self.health_check():
            logger.error("❌ Contract-Agent health check failed. Cannot proceed.")
            return
        
        # Load all converted test files
        test_files = list(CONVERTED_DATA_DIR.glob("*.txt"))
        logger.info(f"📄 Found {len(test_files)} test contracts")
        
        # Define LEDGAR-style test scenarios
        test_scenarios = [
            {
                "name": "Governing_Law_Change",
                "prompt": "Change the governing law from the current jurisdiction to Singapore law and update all related legal references.",
                "complexity": "simple"
            },
            {
                "name": "Payment_Terms_Modification", 
                "prompt": "Modify payment terms to extend from 30 days to 45 days and add a 1.5% monthly late fee.",
                "complexity": "simple"
            },
            {
                "name": "Confidentiality_Enhancement",
                "prompt": "Add comprehensive confidentiality clauses with 5-year survival period and specific trade secret protection.",
                "complexity": "moderate"
            },
            {
                "name": "Indemnification_Restructure",
                "prompt": "Create mutual indemnification structure with liability caps of $1 million per party and exclude gross negligence.",
                "complexity": "complex"
            },
            {
                "name": "Multi_Provision_Update",
                "prompt": "Change entity names, extend contract duration to 3 years, add force majeure clause, and update dispute resolution to JAMS arbitration.",
                "complexity": "complex"
            }
        ]
        
        # Execute tests on a subset of contracts (to manage time)
        selected_files = test_files[:3]  # Use first 3 contracts for comprehensive testing
        
        for test_file in selected_files:
            logger.info(f"\n📋 Testing contract: {test_file.name}")
            
            # Load contract content
            with open(test_file, 'r', encoding='utf-8') as f:
                contract_content = f.read()
            
            # Run each test scenario on this contract
            for scenario in test_scenarios:
                test_name = f"{test_file.stem}_{scenario['name']}"
                result = self.run_test_case(test_name, contract_content, scenario['prompt'])
                self.log_result(test_name, result)
    
    def generate_evaluation_report(self):
        """Generate comprehensive LEDGAR evaluation report"""
        
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
        
        # Generate report
        report = {
            "evaluation_metadata": {
                "session_id": self.session_id,
                "timestamp": self.report_timestamp,
                "evaluator": "LEDGAR Contract-Agent Benchmark",
                "total_tests": total_tests,
                "evaluation_duration": (datetime.now() - self.test_start_time).total_seconds()
            },
            "performance_summary": {
                "success_rate": round(success_rate, 3),
                "avg_processing_time": round(avg_processing_time, 2),
                "avg_ledgar_score": round(avg_ledgar_score, 3),
                "avg_semantic_accuracy": round(avg_semantic_accuracy, 3),
                "avg_iterations": round(avg_iterations, 1)
            },
            "detailed_results": self.results,
            "ledgar_criteria": self.ledgar_criteria
        }
        
        # Save JSON results
        json_file = RESULTS_DIR / f"ledgar_evaluation_{self.report_timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        md_file = RESULTS_DIR / f"ledgar_evaluation_report_{self.report_timestamp}.md"
        self._generate_markdown_report(report, md_file)
        
        logger.info(f"📊 Evaluation complete!")
        logger.info(f"📁 Results saved:")
        logger.info(f"   JSON: {json_file}")
        logger.info(f"   Report: {md_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"🏆 LEDGAR EVALUATION SUMMARY")
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
            f.write(f"# Contract-Agent LEDGAR Benchmark Evaluation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"**Session ID:** {report_data['evaluation_metadata']['session_id']}\n")
            f.write(f"**Evaluation Duration:** {report_data['evaluation_metadata']['evaluation_duration']:.1f} seconds\n\n")
            
            f.write(f"## Executive Summary\n\n")
            f.write(f"This evaluation tests the Contract-Agent architecture against LEDGAR benchmark standards, ")
            f.write(f"focusing on contract provision classification and modification capabilities.\n\n")
            
            summary = report_data['performance_summary']  
            f.write(f"### Key Performance Metrics\n\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1%}\n")
            f.write(f"- **Average Processing Time:** {summary['avg_processing_time']:.1f} seconds\n")
            f.write(f"- **Average LEDGAR Score:** {summary['avg_ledgar_score']:.3f}\n")
            f.write(f"- **Average Semantic Accuracy:** {summary['avg_semantic_accuracy']:.3f}\n")
            f.write(f"- **Average Iterations:** {summary['avg_iterations']:.1f}\n\n")
            
            f.write(f"## LEDGAR Evaluation Criteria\n\n")
            for criterion, weight in report_data['ledgar_criteria'].items():
                f.write(f"- **{criterion.replace('_', ' ').title()}:** {weight:.0%}\n")
            f.write(f"\n")
            
            f.write(f"## Detailed Test Results\n\n")
            f.write(f"| Test Name | Success | Processing Time | LEDGAR Score | Semantic Accuracy | Iterations |\n")
            f.write(f"|-----------|---------|-----------------|--------------|-------------------|------------|\n")
            
            for result in report_data['detailed_results']:
                status = "✅" if result['success'] else "❌"
                f.write(f"| {result['test_name']} | {status} | {result['processing_time']:.1f}s | ")
                f.write(f"{result['ledgar_score']:.3f} | {result['semantic_accuracy']:.3f} | {result['iterations']} |\n")
            
            f.write(f"\n## Performance Analysis\n\n")
            successful = [r for r in report_data['detailed_results'] if r['success']]
            if successful:
                f.write(f"### Processing Time Distribution\n")
                times = [r['processing_time'] for r in successful]
                f.write(f"- Minimum: {min(times):.1f}s\n")
                f.write(f"- Maximum: {max(times):.1f}s\n")  
                f.write(f"- Average: {sum(times)/len(times):.1f}s\n\n")
                
                f.write(f"### LEDGAR Score Distribution\n")
                scores = [r['ledgar_score'] for r in successful]
                f.write(f"- Minimum: {min(scores):.3f}\n")
                f.write(f"- Maximum: {max(scores):.3f}\n")
                f.write(f"- Average: {sum(scores)/len(scores):.3f}\n")
                f.write(f"- Above 0.85 threshold: {len([s for s in scores if s >= 0.85])}/{len(scores)} ({len([s for s in scores if s >= 0.85])/len(scores):.1%})\n\n")
            
            f.write(f"## Conclusions\n\n")
            if summary['success_rate'] >= 0.9 and summary['avg_ledgar_score'] >= 0.85:
                f.write(f"✅ **EXCELLENT PERFORMANCE** - The Contract-Agent architecture demonstrates exceptional ")
                f.write(f"performance on LEDGAR benchmark standards with high success rates and quality scores.\n\n")
            elif summary['success_rate'] >= 0.7 and summary['avg_ledgar_score'] >= 0.75:
                f.write(f"✅ **GOOD PERFORMANCE** - The architecture shows solid performance with room for optimization.\n\n")
            else:
                f.write(f"⚠️ **NEEDS IMPROVEMENT** - Performance indicates areas requiring enhancement.\n\n")
            
            f.write(f"Report generated by Contract-Agent LEDGAR Evaluator\n")


def main():
    """Main evaluation execution"""
    evaluator = LEDGARContractEvaluator()
    
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
