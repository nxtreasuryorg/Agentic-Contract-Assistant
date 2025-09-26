#!/usr/bin/env python3
"""
Simple Contract-Agent API Test
"""

import requests
import time
import json

API_BASE_URL = "http://localhost:5002"

def test_simple_modification():
    # Create a simple RTF content
    simple_contract = """
    Service Agreement
    
    This Service Agreement is entered into between ABC Corp (Provider) and XYZ Inc (Client).
    
    1. Term: This agreement shall remain in effect for 1 year.
    2. Payment: Client shall pay Provider within 30 days.
    3. Governing Law: This agreement shall be governed by New York law.
    
    Signatures:
    _________________
    ABC Corp
    """
    
    # Create RTF format
    rtf_content = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}} \\f0\\fs24 " + simple_contract.replace('\n', '\\par ') + "}"
    
    # Save as temporary RTF file
    temp_file = "/tmp/simple_test.rtf"
    with open(temp_file, 'w') as f:
        f.write(rtf_content)
    
    print("📝 Testing simple contract modification...")
    
    try:
        # Submit processing request
        with open(temp_file, 'rb') as f:
            files = {'file': ('simple_test.rtf', f, 'application/rtf')}
            data = {'prompt': 'Change the governing law from New York to California'}
            
            response = requests.post(f"{API_BASE_URL}/process_contract", 
                                   files=files, data=data, timeout=60)
            
            if response.status_code in [200, 202]:
                result = response.json()
                job_id = result.get('job_id')
                print(f"✅ Job submitted: {job_id}")
                
                # Wait for completion
                max_wait = 120  # 2 minutes
                wait_interval = 5   # 5 seconds
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
                        
                        print(f"⏳ Status: {job_status} ({progress}%) - {waited}s elapsed")
                        
                        if job_status == 'completed':
                            # Get result
                            result_response = requests.get(f"{API_BASE_URL}/job_result/{job_id}")
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                print("✅ SUCCESS!")
                                print(f"📊 Processing completed in {waited}s")
                                print(f"📄 Result success: {result_data.get('success')}")
                                
                                # Show partial result
                                if result_data.get('result'):
                                    final_rtf = result_data['result'].get('final_rtf', '')
                                    print(f"📝 Result length: {len(final_rtf)} characters")
                                    print(f"📋 Sample: {final_rtf[:200]}...")
                                
                                return True
                            break
                        elif job_status == 'failed':
                            print(f"❌ Job failed: {status_data.get('error_message', 'Unknown error')}")
                            break
                    else:
                        print(f"⚠️ Failed to get status: HTTP {status_response.status_code}")
                
                if waited >= max_wait:
                    print(f"⏰ Timeout after {max_wait} seconds")
                
            else:
                print(f"❌ Failed to submit job: HTTP {response.status_code}")
                print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("🧪 Starting simple Contract-Agent API test...")
    
    # Health check first
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health check passed: {health_data['status']}")
        else:
            print(f"❌ Health check failed: HTTP {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        exit(1)
    
    # Run test
    success = test_simple_modification()
    
    if success:
        print("🎉 Simple test completed successfully!")
    else:
        print("💥 Simple test failed!")
