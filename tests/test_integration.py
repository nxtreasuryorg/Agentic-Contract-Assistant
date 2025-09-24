#!/usr/bin/env python3
"""
Test Integration: nxtApp Contract Assistant ↔ Contract-Agent API
"""

import sys
import os
import subprocess
import time
import tempfile
from io import BytesIO

# Add nxtApp to path
sys.path.insert(0, '/home/ec2-user/cb/nxtApp')
sys.path.insert(0, '/home/ec2-user/cb/nxtApp/nxtAppCore')

def create_test_contract():
    """Create a test contract file"""
    contract_content = """
EMPLOYMENT AGREEMENT

This Employment Agreement is entered into between TestCorp Inc., a Delaware corporation 
(the "Company"), and Jane Doe (the "Employee").

1. EMPLOYMENT: Company hereby employs Employee as a Software Developer.
2. COMPENSATION: Company shall pay Employee a base salary of $90,000 per year.
3. GOVERNING LAW: This Agreement shall be governed by the laws of Delaware.

IN WITNESS WHEREOF, the parties have executed this Agreement.
"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(contract_content.strip())
    temp_file.close()
    
    return temp_file.name

def test_contract_processing():
    """Test the complete integration workflow"""
    print("🧪 Testing nxtApp ↔ Contract-Agent Integration")
    print("=" * 60)
    
    # Start Contract-Agent server
    print("🚀 Starting Contract-Agent server...")
    server = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd='/home/ec2-user/cb/Contract-Agent',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Create test file
        test_file_path = create_test_contract()
        print(f"📄 Created test contract: {test_file_path}")
        
        # Test nxtApp contract_assistant
        print("🔄 Testing nxtApp contract processing...")
        
        # Create a mock file object
        class MockFile:
            def __init__(self, filepath):
                self.filename = os.path.basename(filepath)
                with open(filepath, 'rb') as f:
                    self.data = f.read()
            
            def read(self):
                return self.data
                
            def seek(self, pos):
                pass
        
        mock_file = MockFile(test_file_path)
        instruction = "Change TestCorp Inc. to InnovateStart LLC and change Delaware to California"
        
        try:
            from contract_assistant import process_document
            
            print("📤 Processing document...")
            result = process_document(instruction, mock_file)
            
            if result.get('error'):
                print(f"❌ Processing failed: {result['message']}")
                return False
            else:
                print("✅ Processing successful!")
                
                # Check results
                rtf_content = result.get('rtf_content', '')
                stats = result.get('processing_stats', {})
                
                print(f"📊 Processing Stats:")
                print(f"   • Iterations: {stats.get('iterations_used', 'N/A')}")
                print(f"   • Quality Score: {stats.get('final_score', 'N/A')}")
                print(f"   • Chunking Used: {stats.get('chunking_used', False)}")
                
                # Verify changes
                if 'InnovateStart LLC' in rtf_content and 'California' in rtf_content:
                    print("✅ Contract modifications verified!")
                    return True
                else:
                    print("❌ Contract modifications not found")
                    return False
                    
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    finally:
        # Cleanup
        server.terminate()
        server.wait()
        
        try:
            os.unlink(test_file_path)
        except:
            pass
    
if __name__ == "__main__":
    success = test_contract_processing()
    sys.exit(0 if success else 1)
