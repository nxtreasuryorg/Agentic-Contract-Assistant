"""
Demonstration of DocumentChunkingManager integration with Contract Assistant vNext

This script shows how the chunking system would be used within the CrewAI Actor Agent
for processing large contract documents.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from document_chunking import DocumentChunkingManager


class MockActorAgent:
    """Mock Actor Agent to demonstrate chunking integration"""
    
    def __init__(self):
        self.chunking_manager = DocumentChunkingManager()
    
    def process_document(self, document: str, instruction: str) -> str:
        """
        Process document with chunking support (as would be done in CrewAI Actor Agent)
        """
        print(f"Processing document ({len(document)} chars) with instruction: {instruction[:60]}...")
        
        # Check if document needs chunking
        if self.chunking_manager.should_chunk_document(document):
            return self._process_with_chunking(document, instruction)
        else:
            return self._process_single_chunk(document, instruction)
    
    def _process_with_chunking(self, document: str, instruction: str) -> str:
        """Process large document with chunking"""
        print("Document requires chunking - using intelligent chunking strategy")
        
        # Step 1: Find instruction targets
        targets = self.chunking_manager.find_instruction_targets(instruction, document)
        print(f"Found {len(targets)} target sections for prioritization")
        
        # Step 2: Split document into chunks
        chunks = self.chunking_manager.split_document(document)
        print(f"Split document into {len(chunks)} chunks")
        
        # Step 3: Prioritize chunks based on targets
        prioritized_chunks = self.chunking_manager.prioritize_chunks(chunks, targets)
        print("Chunks prioritized based on instruction relevance")
        
        # Step 4: Process chunks in parallel (simulated)
        processed_chunks = self.chunking_manager.process_chunks_parallel(
            prioritized_chunks, 
            instruction, 
            self._process_single_chunk,
            max_workers=5  # Bedrock rate limiting
        )
        
        # Step 5: Reassemble final document
        final_document = self.chunking_manager.reassemble_chunks(processed_chunks)
        
        # Step 6: Validate integrity
        original_chunks = [chunk for chunk, _ in processed_chunks]
        processed_text_chunks = [result for result, _ in processed_chunks]
        integrity_ok = self.chunking_manager.validate_chunk_integrity(chunks, processed_text_chunks)
        
        if not integrity_ok:
            print("⚠️  Warning: Chunk integrity validation failed")
        else:
            print("✅ Chunk integrity validation passed")
        
        return final_document
    
    def _process_single_chunk(self, chunk: str, instruction: str, chunk_id: str = "1/1") -> tuple:
        """
        Simulate processing a single chunk (would call Bedrock in real implementation)
        """
        print(f"  Processing chunk {chunk_id}...")
        
        # Simulate semantic manipulation based on instruction
        processed_chunk = chunk
        changed = False
        
        # Simple simulation of common manipulations
        if "hash blockchain limited" in instruction.lower():
            if "Hash Blockchain Limited" in chunk:
                processed_chunk = chunk.replace("Hash Blockchain Limited", "Digital Finance Corp")
                changed = True
                print(f"    ✓ Applied counterparty change in chunk {chunk_id}")
        
        if "governing law" in instruction.lower() and "hong kong" in instruction.lower():
            if "Hong Kong" in chunk:
                processed_chunk = processed_chunk.replace("Hong Kong", "Singapore")
                changed = True
                print(f"    ✓ Applied governing law change in chunk {chunk_id}")
        
        if "blockchain consulting" in instruction.lower():
            if "blockchain consulting" in chunk:
                processed_chunk = processed_chunk.replace("blockchain consulting", "AI development")
                changed = True
                print(f"    ✓ Applied service type change in chunk {chunk_id}")
        
        return processed_chunk, changed


def demo_small_document():
    """Demonstrate processing of small document (no chunking needed)"""
    print("=== DEMO 1: Small Document Processing ===\n")
    
    # Read sample contract
    with open('test_data/sample_contract.rtf', 'r') as f:
        contract = f.read()
    
    agent = MockActorAgent()
    instruction = "Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp'"
    
    result = agent.process_document(contract, instruction)
    
    print(f"\nOriginal document length: {len(contract)} characters")
    print(f"Processed document length: {len(result)} characters")
    print(f"Changes applied: {'Digital Finance Corp' in result}")
    print("\n" + "="*60 + "\n")


def demo_large_document():
    """Demonstrate processing of large document (chunking required)"""
    print("=== DEMO 2: Large Document Processing with Chunking ===\n")
    
    # Create large contract
    with open('test_data/sample_contract.rtf', 'r') as f:
        base_contract = f.read()
    
    # Make it large enough to require chunking
    large_contract = base_contract
    for i in range(15):
        large_contract += f"\n\nSCHEDULE {chr(65+i)}\n" + base_contract
    
    agent = MockActorAgent()
    instruction = "Change governing law from Hong Kong to Singapore and update all jurisdictional references"
    
    result = agent.process_document(large_contract, instruction)
    
    print(f"\nOriginal document length: {len(large_contract)} characters")
    print(f"Processed document length: {len(result)} characters")
    print(f"Hong Kong references remaining: {result.count('Hong Kong')}")
    print(f"Singapore references added: {result.count('Singapore')}")
    print("\n" + "="*60 + "\n")


def demo_complex_instruction():
    """Demonstrate processing with complex multi-part instruction"""
    print("=== DEMO 3: Complex Multi-Part Instruction ===\n")
    
    # Create medium-sized contract
    with open('test_data/sample_contract.rtf', 'r') as f:
        base_contract = f.read()
    
    medium_contract = base_contract
    for i in range(8):
        medium_contract += f"\n\nADDENDUM {i+1}\n" + base_contract
    
    agent = MockActorAgent()
    complex_instruction = """
    1. Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp'
    2. Update governing law from Hong Kong to Singapore
    3. Replace 'blockchain consulting services' with 'AI development services'
    """
    
    result = agent.process_document(medium_contract, complex_instruction)
    
    print(f"\nOriginal document length: {len(medium_contract)} characters")
    print(f"Processed document length: {len(result)} characters")
    
    # Check all changes
    changes_applied = []
    if "Digital Finance Corp" in result:
        changes_applied.append("✓ Counterparty name changed")
    if "Singapore" in result and result.count("Hong Kong") < medium_contract.count("Hong Kong"):
        changes_applied.append("✓ Governing law updated")
    if "AI development" in result:
        changes_applied.append("✓ Service type changed")
    
    print("Changes applied:")
    for change in changes_applied:
        print(f"  {change}")
    
    print("\n" + "="*60 + "\n")


def demo_performance_comparison():
    """Demonstrate performance benefits of chunking vs single processing"""
    print("=== DEMO 4: Performance Comparison ===\n")
    
    # Create very large contract
    with open('test_data/sample_contract.rtf', 'r') as f:
        base_contract = f.read()
    
    very_large_contract = base_contract
    for i in range(25):  # Make it very large
        very_large_contract += f"\n\nSECTION {i+1}\n" + base_contract
    
    print(f"Very large contract: {len(very_large_contract)} characters")
    
    agent = MockActorAgent()
    instruction = "Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp'"
    
    # Simulate timing (in real implementation, this would show actual performance benefits)
    import time
    
    start_time = time.time()
    result = agent.process_document(very_large_contract, instruction)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    print(f"Final document length: {len(result)} characters")
    print(f"Parallel processing enabled: {len(very_large_contract) > 25000}")
    
    # Show chunking statistics
    manager = DocumentChunkingManager()
    chunks = manager.split_document(very_large_contract)
    print(f"Document was split into {len(chunks)} chunks for parallel processing")
    print(f"Average chunk size: {sum(len(c) for c in chunks) // len(chunks)} characters")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("DocumentChunkingManager Integration Demonstration")
    print("=" * 60)
    print()
    
    try:
        demo_small_document()
        demo_large_document()
        demo_complex_instruction()
        demo_performance_comparison()
        
        print("🎉 All demonstrations completed successfully!")
        print("\nKey Benefits Demonstrated:")
        print("✓ Automatic chunking decision based on document size")
        print("✓ Intelligent target identification from instructions")
        print("✓ Chunk prioritization for relevant content")
        print("✓ Parallel processing with rate limiting")
        print("✓ Document reassembly with integrity validation")
        print("✓ Seamless integration with Actor Agent workflow")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)