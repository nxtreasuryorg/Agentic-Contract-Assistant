#!/usr/bin/env python3
"""
Test the fixed Contract-Agent version
"""

import requests
import time
import json

API_BASE_URL = "http://localhost:5002"

def test_simple_contract():
    """Test simple contract modification"""
    print("🧪 Testing fixed Contract-Agent version...")
    
    # Simple contract content
    contract_text = """
    SERVICE AGREEMENT
    
    This Service Agreement is entered into between ABC Corporation ("Provider") 
    and XYZ Industries ("Client") on January 1, 2025.
    
    1. SERVICES: Provider shall deliver consulting services.
    2. PAYMENT: Client shall pay Provider $10,000 per month.
    3. TERM: This agreement is effective for 1 year.
    4. GOVERNING LAW: This agreement is governed by New York law.
    
    Signed:
    ABC Corporation
    XYZ Industries
    """
    
    # Create RTF
    rtf_content = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}} \\f0\\fs24 " + contract_text.replace('\n', '\\par ') + "}"
    
    # Save RTF file
    temp_file = "/tmp/test_contract.rtf"
    with open(temp_file, 'w') as f:
        f.write(rtf_content)
    
    # Test modification
    test_cases = [
        {
            "name": "Simple Entity Change",
            "prompt": "Change ABC Corporation to TechCorp Solutions throughout the document"
        },
        {
            "name": "Jurisdiction Change",
            "prompt": "Change governing law from New York to California"
        },
        {
            "name": "Payment Terms",
            "prompt": "Change payment from $10,000 to $15,000 per month"
        }
    ]
    
    for test in test_cases:
        print(f"\n📝 Testing: {test['name']}")
        print(f"   Prompt: {test['prompt']}")
        
        try:
            # Submit job
            with open(temp_file, 'rb') as f:
                files = {'file': ('test.rtf', f, 'application/rtf')}
                data = {'prompt': test['prompt']}
                
                response = requests.post(f"{API_BASE_URL}/process_contract", 
                                       files=files, data=data, timeout=30)
                
                if response.status_code in [200, 202]:
                    result = response.json()
                    job_id = result.get('job_id')
                    print(f"   ✅ Job submitted: {job_id}")
                    
                    # Wait for completion
                    max_wait = 120
                    wait_interval = 5
                    waited = 0
                    
                    while waited < max_wait:
                        time.sleep(wait_interval)
                        waited += wait_interval
                        
                        # Check status
                        status_response = requests.get(f"{API_BASE_URL}/job_status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            job_status = status_data.get('status')
                            progress = status_data.get('progress', 0)
                            
                            print(f"   ⏳ Status: {job_status} ({progress}%) - {waited}s")
                            
                            if job_status == 'completed':
                                print(f"   ✅ SUCCESS - Job completed in {waited}s")
                                
                                # Get result
                                result_response = requests.get(f"{API_BASE_URL}/job_result/{job_id}")
                                if result_response.status_code == 200:
                                    result_data = result_response.json()
                                    if result_data.get('success'):
                                        print(f"   📊 Quality Score: {result_data.get('result', {}).get('final_score', 'N/A')}")
                                        print(f"   🔄 Iterations: {result_data.get('result', {}).get('iterations_used', 'N/A')}")
                                break
                                
                            elif job_status == 'failed':
                                error_msg = status_data.get('error_message', 'Unknown error')
                                print(f"   ❌ FAILED: {error_msg}")
                                break
                    
                    if waited >= max_wait:
                        print(f"   ⏰ TIMEOUT after {max_wait}s")
                        
                else:
                    print(f"   ❌ Failed to submit: HTTP {response.status_code}")
                    print(f"   Response: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Check metrics
    print("\n📊 Checking performance metrics...")
    metrics_response = requests.get(f"{API_BASE_URL}/metrics")
    if metrics_response.status_code == 200:
        metrics = metrics_response.json()
        stats = metrics.get('statistics', {})
        print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
        print(f"   Success Rate: {stats.get('success_rate', 0):.1%}")
        print(f"   Avg Processing Time: {stats.get('avg_processing_time', 0):.1f}s")
        print(f"   Avg Quality Score: {stats.get('avg_quality_score', 0):.2f}")
        print(f"   Error Breakdown: {stats.get('error_breakdown', {})}")


if __name__ == "__main__":
    # Health check first
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Health check passed: {health['status']}")
            print(f"   Performance metrics available: {bool(health.get('performance_metrics'))}")
        else:
            print(f"❌ Health check failed: HTTP {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to Contract-Agent: {str(e)}")
        exit(1)
    
    # Run tests
    test_simple_contract()
    print("\n🎉 Testing completed!")
