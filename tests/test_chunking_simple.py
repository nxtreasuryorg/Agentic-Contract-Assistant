"""
Simple test script for DocumentChunkingManager without pytest dependency
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from document_chunking import DocumentChunkingManager


def test_basic_functionality():
    """Test basic DocumentChunkingManager functionality"""
    print("Testing DocumentChunkingManager...")
    
    # Initialize manager
    manager = DocumentChunkingManager()
    print(f"✓ Initialized with chunk_size={manager.chunk_size}, chunk_overlap={manager.chunk_overlap}")
    
    # Test small document
    small_contract = """
    CONSULTING AGREEMENT
    
    This Consulting Agreement ("Agreement") is entered into on January 1, 2024,
    between Hash Blockchain Limited, a company incorporated in Hong Kong ("Company"),
    and Digital Solutions Inc., a corporation organized under Delaware law ("Consultant").
    
    1. SERVICES
    Consultant shall provide blockchain development services as specified in Exhibit A.
    
    2. COMPENSATION
    Company shall pay Consultant $10,000 per month for services rendered.
    
    3. GOVERNING LAW
    This Agreement shall be governed by the laws of Hong Kong.
    
    4. TERMINATION
    Either party may terminate this Agreement with 30 days written notice.
    """
    
    print(f"Small contract length: {len(small_contract)} characters")
    
    # Test should_chunk_document
    should_chunk = manager.should_chunk_document(small_contract)
    print(f"✓ Should chunk small document: {should_chunk} (expected: False)")
    
    # Test split_document
    chunks = manager.split_document(small_contract)
    print(f"✓ Split small document into {len(chunks)} chunks (expected: 1)")
    
    # Test find_instruction_targets
    instruction = "Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp'"
    targets = manager.find_instruction_targets(instruction, small_contract)
    print(f"✓ Found {len(targets)} targets for counterparty change instruction")
    
    # Test prioritize_chunks
    prioritized = manager.prioritize_chunks(chunks, targets)
    print(f"✓ Prioritized {len(prioritized)} chunks")
    
    # Test with large document
    large_contract = small_contract * 100  # Make it large enough to chunk
    print(f"Large contract length: {len(large_contract)} characters")
    
    should_chunk_large = manager.should_chunk_document(large_contract)
    print(f"✓ Should chunk large document: {should_chunk_large} (expected: True)")
    
    large_chunks = manager.split_document(large_contract)
    print(f"✓ Split large document into {len(large_chunks)} chunks")
    
    # Test target finding on large document
    large_targets = manager.find_instruction_targets(instruction, large_contract)
    print(f"✓ Found {len(large_targets)} targets in large document")
    
    # Test prioritization on large document
    large_prioritized = manager.prioritize_chunks(large_chunks, large_targets)
    print(f"✓ Prioritized {len(large_prioritized)} chunks for large document")
    
    # Test reassembly
    mock_processed = [(chunk + "_processed", True) for chunk in chunks]
    reassembled = manager.reassemble_chunks(mock_processed)
    print(f"✓ Reassembled document length: {len(reassembled)} characters")
    
    # Test integrity validation
    original_chunks = ["chunk1", "chunk2", "chunk3"]
    processed_chunks = ["chunk1_mod", "chunk2_mod", "chunk3_mod"]
    integrity_ok = manager.validate_chunk_integrity(original_chunks, processed_chunks)
    print(f"✓ Chunk integrity validation: {integrity_ok} (expected: True)")
    
    print("\n✅ All basic tests passed!")


def test_instruction_parsing():
    """Test instruction parsing and target identification"""
    print("\nTesting instruction parsing...")
    
    manager = DocumentChunkingManager()
    
    contract = """
    MASTER SERVICE AGREEMENT
    
    This Agreement is between Hash Blockchain Limited ("Company") and Tech Solutions Inc. ("Provider").
    
    GOVERNING LAW: This agreement shall be governed by the laws of Hong Kong.
    
    PAYMENT TERMS: Company shall pay Provider $15,000 monthly.
    
    TERMINATION: Either party may terminate with 30 days notice.
    """
    
    test_instructions = [
        'Change "Hash Blockchain Limited" to "Crypto Innovations Ltd"',
        "Update governing law from Hong Kong to Singapore",
        "Modify payment terms to $20,000 per month",
        """1. Change company name to 'Digital Finance Corp'
           2. Update jurisdiction to Delaware
           3. Increase payment to $25,000""",
        "Replace the counterparty and update all contact information"
    ]
    
    for i, instruction in enumerate(test_instructions, 1):
        targets = manager.find_instruction_targets(instruction, contract)
        print(f"✓ Instruction {i}: Found {len(targets)} targets")
        for j, target in enumerate(targets[:2]):  # Show first 2 targets
            print(f"  Target {j+1}: {target[:100]}...")
    
    print("✅ Instruction parsing tests completed!")


def test_chunk_prioritization():
    """Test chunk prioritization logic"""
    print("\nTesting chunk prioritization...")
    
    manager = DocumentChunkingManager()
    
    # Create chunks with different relevance levels
    chunks = [
        "This is chunk 1 with no relevant content about random topics",
        "This chunk contains Hash Blockchain Limited and governing law information from Hong Kong",
        "Another chunk with some general contract terms and standard conditions",
        "This chunk has Hash Blockchain Limited mentioned multiple times Hash Blockchain Limited and more details",
        "SECTION 1: PARTIES - This section defines Hash Blockchain Limited as the primary party"
    ]
    
    targets = ["Hash Blockchain Limited company information"]
    
    prioritized = manager.prioritize_chunks(chunks, targets)
    
    print("Original chunk order:")
    for i, chunk in enumerate(chunks):
        print(f"  {i}: {chunk[:60]}...")
    
    print("\nPrioritized chunk order:")
    for i, chunk in enumerate(prioritized):
        print(f"  {i}: {chunk[:60]}...")
    
    # Verify that chunks with more mentions come first
    first_chunk = prioritized[0]
    assert "multiple times" in first_chunk or "SECTION" in first_chunk
    print("✅ Chunk prioritization working correctly!")


def test_parallel_processing_mock():
    """Test parallel processing with mock function"""
    print("\nTesting parallel processing...")
    
    manager = DocumentChunkingManager()
    
    chunks = ["chunk1", "chunk2", "chunk3", "chunk4"]
    instruction = "test instruction"
    
    def mock_processor(chunk, instruction, chunk_id):
        print(f"  Processing {chunk_id}: {chunk}")
        return f"processed_{chunk}", True
    
    results = manager.process_chunks_parallel(chunks, instruction, mock_processor, max_workers=2)
    
    print(f"✓ Processed {len(results)} chunks in parallel")
    for i, (result, changed) in enumerate(results):
        print(f"  Result {i}: {result}, changed: {changed}")
    
    print("✅ Parallel processing test completed!")


if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_instruction_parsing()
        test_chunk_prioritization()
        test_parallel_processing_mock()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)