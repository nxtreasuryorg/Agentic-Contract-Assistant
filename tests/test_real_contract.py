"""
Test DocumentChunkingManager with real RTF contract document
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from document_chunking import DocumentChunkingManager


def test_with_real_contract():
    """Test with the actual RTF contract from test_data"""
    print("Testing with real RTF contract...")
    
    # Read the sample contract
    with open('test_data/sample_contract.rtf', 'r') as f:
        rtf_contract = f.read()
    
    print(f"RTF contract length: {len(rtf_contract)} characters")
    
    manager = DocumentChunkingManager()
    
    # Test various instruction types
    instructions = [
        "Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp'",
        "Change governing law from Hong Kong to Singapore, update all jurisdictional references",
        "Shift liability from company to client, reverse indemnification clauses",
        'Replace "blockchain consulting services" with "AI development services"',
        """1. Change company name from 'Hash Blockchain Limited' to 'Crypto Innovations Ltd'
           2. Update governing law to Delaware
           3. Modify the client name to 'Tech Partners LLC'""",
        "Change the counterparty from 'Digital Solutions Corp' to 'Innovation Partners Inc' and update all contact information"
    ]
    
    for i, instruction in enumerate(instructions, 1):
        print(f"\n--- Testing Instruction {i} ---")
        print(f"Instruction: {instruction[:80]}...")
        
        # Find targets
        targets = manager.find_instruction_targets(instruction, rtf_contract)
        print(f"Found {len(targets)} target sections")
        
        # Show first target if found
        if targets:
            print(f"First target preview: {targets[0][:100]}...")
        
        # Test chunking decision
        should_chunk = manager.should_chunk_document(rtf_contract)
        print(f"Should chunk: {should_chunk}")
        
        # Split document
        chunks = manager.split_document(rtf_contract)
        print(f"Document split into {len(chunks)} chunks")
        
        # Prioritize chunks
        prioritized = manager.prioritize_chunks(chunks, targets)
        print(f"Chunks prioritized, first chunk score calculated")
        
        # Show chunk priorities if multiple chunks
        if len(chunks) > 1:
            print("Chunk prioritization preview:")
            for j, chunk in enumerate(prioritized[:3]):  # Show first 3
                preview = chunk.replace('\n', ' ').replace('\r', '')[:60]
                print(f"  Chunk {j}: {preview}...")
    
    print("\n✅ Real contract testing completed!")


def test_large_contract_chunking():
    """Test chunking with artificially large contract"""
    print("\nTesting large contract chunking...")
    
    # Read the sample contract and make it large
    with open('test_data/sample_contract.rtf', 'r') as f:
        base_contract = f.read()
    
    # Create a large contract by repeating sections
    large_contract = base_contract
    for i in range(20):  # Repeat to make it large enough
        large_contract += f"\n\nADDENDUM {i+1}\n" + base_contract
    
    print(f"Large contract length: {len(large_contract)} characters")
    
    manager = DocumentChunkingManager()
    
    # Test chunking
    should_chunk = manager.should_chunk_document(large_contract)
    print(f"Should chunk large contract: {should_chunk}")
    
    if should_chunk:
        chunks = manager.split_document(large_contract)
        print(f"Split into {len(chunks)} chunks")
        
        # Test with complex instruction
        instruction = "Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp' and update governing law from Hong Kong to Singapore"
        
        targets = manager.find_instruction_targets(instruction, large_contract)
        print(f"Found {len(targets)} targets in large contract")
        
        prioritized = manager.prioritize_chunks(chunks, targets)
        print(f"Prioritized {len(prioritized)} chunks")
        
        # Test parallel processing simulation
        def mock_processor(chunk, instruction, chunk_id):
            # Simulate processing by adding a marker
            return chunk + f"\n[PROCESSED BY {chunk_id}]", True
        
        print("Testing parallel processing simulation...")
        results = manager.process_chunks_parallel(
            chunks[:3],  # Test with first 3 chunks only
            instruction, 
            mock_processor, 
            max_workers=2
        )
        
        print(f"Processed {len(results)} chunks in parallel")
        
        # Test reassembly
        reassembled = manager.reassemble_chunks(results)
        print(f"Reassembled length: {len(reassembled)} characters")
        
        # Test integrity validation
        original_chunks = chunks[:3]
        processed_chunks = [result[0] for result in results]
        integrity_ok = manager.validate_chunk_integrity(original_chunks, processed_chunks)
        print(f"Chunk integrity validation: {integrity_ok}")
    
    print("✅ Large contract chunking test completed!")


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\nTesting edge cases...")
    
    manager = DocumentChunkingManager()
    
    # Test empty document
    empty_targets = manager.find_instruction_targets("test", "")
    print(f"✓ Empty document targets: {len(empty_targets)}")
    
    # Test empty instruction
    empty_instruction_targets = manager.find_instruction_targets("", "some document content")
    print(f"✓ Empty instruction targets: {len(empty_instruction_targets)}")
    
    # Test very short document
    short_doc = "Short contract"
    short_chunks = manager.split_document(short_doc)
    print(f"✓ Short document chunks: {len(short_chunks)}")
    
    # Test reassembly with empty list
    empty_reassembly = manager.reassemble_chunks([])
    print(f"✓ Empty reassembly result: '{empty_reassembly}'")
    
    # Test prioritization with no targets
    test_chunks = ["chunk1", "chunk2", "chunk3"]
    no_target_priority = manager.prioritize_chunks(test_chunks, [])
    print(f"✓ No targets prioritization: {len(no_target_priority)} chunks (same order)")
    
    print("✅ Edge cases testing completed!")


if __name__ == "__main__":
    try:
        test_with_real_contract()
        test_large_contract_chunking()
        test_edge_cases()
        print("\n🎉 All real contract tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)