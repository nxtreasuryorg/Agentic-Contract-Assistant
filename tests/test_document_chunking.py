"""
Test suite for DocumentChunkingManager

Tests all functionality including chunking, target identification, prioritization,
and parallel processing with various contract document types and instruction patterns.
"""

import pytest
import os
from unittest.mock import Mock, patch
from document_chunking import DocumentChunkingManager


class TestDocumentChunkingManager:
    """Test suite for DocumentChunkingManager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.chunking_manager = DocumentChunkingManager()
        
        # Sample small contract (under 25k chars)
        self.small_contract = """
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
        
        # Sample large contract (over 25k chars)
        self.large_contract = self._generate_large_contract()
        
        # Sample instructions for testing
        self.instructions = {
            "counterparty_change": "Change all references from 'Hash Blockchain Limited' to 'Digital Finance Corp'",
            "domicile_shift": "Change governing law from Hong Kong to Singapore, update all jurisdictional references",
            "liability_change": "Shift liability from company to client, reverse indemnification clauses",
            "multi_part": """1. Change company name from 'Hash Blockchain Limited' to 'Crypto Innovations Ltd'
                           2. Update governing law to Delaware
                           3. Modify payment terms to $15,000 per month""",
            "quoted_text": 'Replace "blockchain development services" with "AI consulting services"',
            "complex_semantic": "Change the counterparty from 'Digital Solutions Inc.' to 'Tech Partners LLC' and update all contact information accordingly"
        }
    
    def _generate_large_contract(self) -> str:
        """Generate a large contract document for testing chunking"""
        base_contract = """
        MASTER SERVICE AGREEMENT
        
        This Master Service Agreement ("Agreement") is entered into on January 1, 2024,
        between Hash Blockchain Limited, a company incorporated in Hong Kong ("Company"),
        and Digital Solutions Inc., a corporation organized under Delaware law ("Service Provider").
        
        RECITALS
        
        WHEREAS, Company desires to engage Service Provider to provide certain services;
        WHEREAS, Service Provider has the expertise and capability to provide such services;
        
        NOW, THEREFORE, in consideration of the mutual covenants contained herein, the parties agree:
        
        1. DEFINITIONS
        
        1.1 "Affiliate" means, with respect to any entity, any other entity that directly or indirectly
        controls, is controlled by, or is under common control with, such entity.
        
        1.2 "Confidential Information" means all non-public, proprietary or confidential information
        disclosed by one party to the other party.
        
        1.3 "Services" means the services to be provided by Service Provider as described in
        each Statement of Work executed under this Agreement.
        
        2. SERVICES AND DELIVERABLES
        
        2.1 Service Provider shall provide the Services in accordance with the terms and conditions
        of this Agreement and the applicable Statement of Work.
        
        2.2 All Services shall be performed in a professional and workmanlike manner in accordance
        with industry standards and best practices.
        
        2.3 Service Provider shall provide all personnel, equipment, and materials necessary to
        perform the Services, unless otherwise specified in a Statement of Work.
        
        3. COMPENSATION AND PAYMENT TERMS
        
        3.1 Company shall pay Service Provider the fees specified in each Statement of Work.
        
        3.2 Unless otherwise specified, all fees are due within thirty (30) days of receipt of
        Service Provider's invoice.
        
        3.3 All fees are exclusive of applicable taxes, which shall be paid by Company.
        
        4. INTELLECTUAL PROPERTY
        
        4.1 All work product, inventions, and intellectual property created by Service Provider
        in the performance of Services shall be owned by Company.
        
        4.2 Service Provider hereby assigns to Company all right, title, and interest in and to
        such work product and intellectual property.
        
        5. CONFIDENTIALITY
        
        5.1 Each party acknowledges that it may have access to Confidential Information of the other party.
        
        5.2 Each party agrees to maintain the confidentiality of such Confidential Information and
        not to disclose it to any third party without prior written consent.
        
        6. WARRANTIES AND REPRESENTATIONS
        
        6.1 Each party represents and warrants that it has the full corporate power and authority
        to enter into this Agreement.
        
        6.2 Service Provider warrants that the Services will be performed in accordance with
        industry standards and will be free from material defects.
        
        7. INDEMNIFICATION
        
        7.1 Service Provider shall indemnify, defend, and hold harmless Company from and against
        any claims, damages, losses, and expenses arising from Service Provider's breach of this Agreement.
        
        7.2 Company shall indemnify, defend, and hold harmless Service Provider from and against
        any claims arising from Company's use of the Services in violation of applicable law.
        
        8. LIMITATION OF LIABILITY
        
        8.1 IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
        CONSEQUENTIAL, OR PUNITIVE DAMAGES.
        
        8.2 EACH PARTY'S TOTAL LIABILITY SHALL NOT EXCEED THE TOTAL AMOUNT PAID OR PAYABLE
        UNDER THIS AGREEMENT IN THE TWELVE MONTHS PRECEDING THE CLAIM.
        
        9. TERM AND TERMINATION
        
        9.1 This Agreement shall commence on the Effective Date and continue until terminated
        in accordance with its terms.
        
        9.2 Either party may terminate this Agreement for convenience with sixty (60) days
        written notice to the other party.
        
        9.3 Either party may terminate this Agreement immediately upon written notice if the
        other party materially breaches this Agreement and fails to cure such breach within
        thirty (30) days after written notice.
        
        10. GOVERNING LAW AND DISPUTE RESOLUTION
        
        10.1 This Agreement shall be governed by and construed in accordance with the laws of Hong Kong.
        
        10.2 Any disputes arising under this Agreement shall be resolved through binding arbitration
        in Hong Kong under the rules of the Hong Kong International Arbitration Centre.
        
        11. GENERAL PROVISIONS
        
        11.1 This Agreement constitutes the entire agreement between the parties with respect to
        the subject matter hereof.
        
        11.2 This Agreement may not be amended except by written agreement signed by both parties.
        
        11.3 If any provision of this Agreement is held to be invalid or unenforceable, the
        remaining provisions shall remain in full force and effect.
        
        11.4 This Agreement shall be binding upon and inure to the benefit of the parties and
        their respective successors and assigns.
        
        IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.
        
        HASH BLOCKCHAIN LIMITED          DIGITAL SOLUTIONS INC.
        
        By: _________________________    By: _________________________
        Name: John Smith                 Name: Jane Doe
        Title: Chief Executive Officer   Title: President
        Date: January 1, 2024           Date: January 1, 2024
        """
        
        # Repeat the contract multiple times to make it large enough for chunking
        return (base_contract + "\n\n" + "ADDITIONAL TERMS AND CONDITIONS\n" + base_contract) * 10
    
    def test_initialization(self):
        """Test DocumentChunkingManager initialization"""
        manager = DocumentChunkingManager()
        assert manager.chunk_size == 25000
        assert manager.chunk_overlap == 5000
        assert manager.text_splitter is not None
        
        # Test custom initialization
        custom_manager = DocumentChunkingManager(chunk_size=10000, chunk_overlap=2000)
        assert custom_manager.chunk_size == 10000
        assert custom_manager.chunk_overlap == 2000
    
    def test_should_chunk_document(self):
        """Test document chunking decision logic"""
        # Small document should not be chunked
        assert not self.chunking_manager.should_chunk_document(self.small_contract)
        
        # Large document should be chunked
        assert self.chunking_manager.should_chunk_document(self.large_contract)
        
        # Edge case: exactly at threshold
        threshold_text = "x" * 25000
        assert self.chunking_manager.should_chunk_document(threshold_text)
        
        # Just under threshold
        under_threshold_text = "x" * 24999
        assert not self.chunking_manager.should_chunk_document(under_threshold_text)
    
    def test_split_document_small(self):
        """Test document splitting for small documents"""
        chunks = self.chunking_manager.split_document(self.small_contract)
        
        # Small document should return as single chunk
        assert len(chunks) == 1
        assert chunks[0] == self.small_contract
    
    def test_split_document_large(self):
        """Test document splitting for large documents"""
        chunks = self.chunking_manager.split_document(self.large_contract)
        
        # Large document should be split into multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be within size limits (allowing for some variance due to splitting logic)
        for chunk in chunks:
            assert len(chunk) <= self.chunking_manager.chunk_size + 1000  # Allow some variance
        
        # Verify chunks can be reassembled (basic check)
        reassembled = "".join(chunks)
        # Due to overlap, reassembled might be longer, but should contain original content
        assert len(reassembled) >= len(self.large_contract)
    
    def test_find_instruction_targets_quoted_text(self):
        """Test target identification with quoted text"""
        instruction = self.instructions["quoted_text"]
        targets = self.chunking_manager.find_instruction_targets(instruction, self.small_contract)
        
        # Should find targets related to "blockchain development services"
        assert len(targets) > 0
        
        # Targets should contain relevant context
        found_relevant = any("blockchain" in target.lower() for target in targets)
        assert found_relevant
    
    def test_find_instruction_targets_counterparty_change(self):
        """Test target identification for counterparty changes"""
        instruction = self.instructions["counterparty_change"]
        targets = self.chunking_manager.find_instruction_targets(instruction, self.small_contract)
        
        # Should find targets related to "Hash Blockchain Limited"
        assert len(targets) > 0
        
        # Targets should contain the company name
        found_company = any("hash blockchain" in target.lower() for target in targets)
        assert found_company
    
    def test_find_instruction_targets_governing_law(self):
        """Test target identification for governing law changes"""
        instruction = self.instructions["domicile_shift"]
        targets = self.chunking_manager.find_instruction_targets(instruction, self.small_contract)
        
        # Should find targets related to governing law
        assert len(targets) > 0
        
        # Targets should contain governing law context
        found_law = any("governing law" in target.lower() or "hong kong" in target.lower() for target in targets)
        assert found_law
    
    def test_find_instruction_targets_multi_part(self):
        """Test target identification for multi-part instructions"""
        instruction = self.instructions["multi_part"]
        targets = self.chunking_manager.find_instruction_targets(instruction, self.small_contract)
        
        # Should find multiple targets for different parts of instruction
        assert len(targets) > 0
        
        # Should find targets for company name, governing law, and payment terms
        target_text = " ".join(targets).lower()
        assert "hash blockchain" in target_text or "company" in target_text
    
    def test_prioritize_chunks_no_targets(self):
        """Test chunk prioritization with no targets"""
        chunks = ["chunk1", "chunk2", "chunk3"]
        targets = []
        
        prioritized = self.chunking_manager.prioritize_chunks(chunks, targets)
        
        # Should return original chunks when no targets
        assert prioritized == chunks
    
    def test_prioritize_chunks_with_targets(self):
        """Test chunk prioritization with relevant targets"""
        # Create chunks with different relevance levels
        chunks = [
            "This is chunk 1 with no relevant content",
            "This chunk contains Hash Blockchain Limited and governing law information",
            "Another chunk with some contract terms and conditions",
            "This chunk has Hash Blockchain Limited mentioned multiple times Hash Blockchain Limited"
        ]
        
        targets = ["Hash Blockchain Limited company information"]
        
        prioritized = self.chunking_manager.prioritize_chunks(chunks, targets)
        
        # Most relevant chunks should come first
        assert len(prioritized) == len(chunks)
        
        # Chunk with multiple mentions should be prioritized higher
        assert "multiple times" in prioritized[0]
    
    def test_prioritize_chunks_structure_markers(self):
        """Test chunk prioritization based on contract structure markers"""
        chunks = [
            "Random text without structure",
            "SECTION 1: PARTIES - This section defines the parties to the agreement",
            "Some middle content",
            "GOVERNING LAW - This agreement shall be governed by applicable law"
        ]
        
        targets = []  # No specific targets, should prioritize based on structure
        
        prioritized = self.chunking_manager.prioritize_chunks(chunks, targets)
        
        # Chunks with structure markers should be prioritized
        # The exact order depends on scoring, but structured chunks should come first
        structured_chunks = [chunk for chunk in prioritized if any(marker in chunk.upper() for marker in ["SECTION", "GOVERNING LAW"])]
        assert len(structured_chunks) >= 2
    
    def test_process_chunks_parallel_mock(self):
        """Test parallel chunk processing with mocked processor function"""
        chunks = ["chunk1", "chunk2", "chunk3"]
        instruction = "test instruction"
        
        # Mock processor function
        def mock_processor(chunk, instruction, chunk_id):
            return f"processed_{chunk}", True
        
        results = self.chunking_manager.process_chunks_parallel(
            chunks, instruction, mock_processor, max_workers=2
        )
        
        # Should return results for all chunks
        assert len(results) == len(chunks)
        
        # Each result should be a tuple (processed_text, changed_flag)
        for i, (processed_text, changed) in enumerate(results):
            assert processed_text == f"processed_chunk{i+1}"
            assert changed is True
    
    def test_process_chunks_parallel_error_handling(self):
        """Test parallel processing error handling"""
        chunks = ["chunk1", "chunk2", "chunk3"]
        instruction = "test instruction"
        
        # Mock processor function that raises errors
        def error_processor(chunk, instruction, chunk_id):
            if "chunk2" in chunk:
                raise Exception("Processing error")
            return f"processed_{chunk}", True
        
        results = self.chunking_manager.process_chunks_parallel(
            chunks, instruction, error_processor, max_workers=2
        )
        
        # Should handle errors gracefully
        assert len(results) == len(chunks)
        
        # Error chunk should return original content
        assert results[1] == ("chunk2", False)  # Error case
        assert results[0] == ("processed_chunk1", True)  # Success case
        assert results[2] == ("processed_chunk3", True)  # Success case
    
    def test_process_chunks_parallel_aws_credentials_error(self):
        """Test parallel processing with AWS credentials error"""
        chunks = ["chunk1", "chunk2"]
        instruction = "test instruction"
        
        # Mock processor function that raises AWS credentials error
        def aws_error_processor(chunk, instruction, chunk_id):
            raise Exception("AWS Credentials Error: Invalid security token")
        
        # Should raise the AWS credentials error
        with pytest.raises(Exception, match="AWS Bedrock credentials error"):
            self.chunking_manager.process_chunks_parallel(
                chunks, instruction, aws_error_processor, max_workers=1
            )
    
    def test_reassemble_chunks_simple(self):
        """Test basic chunk reassembly"""
        processed_chunks = [
            ("chunk1_processed", True),
            ("chunk2_processed", False),
            ("chunk3_processed", True)
        ]
        
        result = self.chunking_manager.reassemble_chunks(processed_chunks)
        
        assert result == "chunk1_processedchunk2_processedchunk3_processed"
    
    def test_reassemble_chunks_text_only(self):
        """Test chunk reassembly with text-only input"""
        processed_chunks = ["chunk1", "chunk2", "chunk3"]
        
        result = self.chunking_manager.reassemble_chunks(processed_chunks)
        
        assert result == "chunk1chunk2chunk3"
    
    def test_reassemble_chunks_empty(self):
        """Test chunk reassembly with empty input"""
        result = self.chunking_manager.reassemble_chunks([])
        assert result == ""
    
    def test_validate_chunk_integrity_success(self):
        """Test successful chunk integrity validation"""
        original_chunks = ["chunk1", "chunk2", "chunk3"]
        processed_chunks = ["chunk1_modified", "chunk2_modified", "chunk3_modified"]
        
        result = self.chunking_manager.validate_chunk_integrity(original_chunks, processed_chunks)
        assert result is True
    
    def test_validate_chunk_integrity_count_mismatch(self):
        """Test chunk integrity validation with count mismatch"""
        original_chunks = ["chunk1", "chunk2", "chunk3"]
        processed_chunks = ["chunk1_modified", "chunk2_modified"]  # Missing one chunk
        
        result = self.chunking_manager.validate_chunk_integrity(original_chunks, processed_chunks)
        assert result is False
    
    def test_validate_chunk_integrity_size_change(self):
        """Test chunk integrity validation with significant size change"""
        original_chunks = ["short", "text", "here"]
        processed_chunks = ["very long processed text" * 100, "another very long processed text" * 100, "third very long processed text" * 100]
        
        result = self.chunking_manager.validate_chunk_integrity(original_chunks, processed_chunks)
        assert result is False  # Size change > 50%
    
    def test_end_to_end_small_document(self):
        """Test end-to-end processing for small document"""
        instruction = self.instructions["counterparty_change"]
        
        # Should not chunk small document
        assert not self.chunking_manager.should_chunk_document(self.small_contract)
        
        # Find targets
        targets = self.chunking_manager.find_instruction_targets(instruction, self.small_contract)
        assert len(targets) > 0
        
        # Split document (should return single chunk)
        chunks = self.chunking_manager.split_document(self.small_contract)
        assert len(chunks) == 1
        
        # Prioritize (should return same chunk)
        prioritized = self.chunking_manager.prioritize_chunks(chunks, targets)
        assert prioritized == chunks
    
    def test_end_to_end_large_document(self):
        """Test end-to-end processing for large document"""
        instruction = self.instructions["counterparty_change"]
        
        # Should chunk large document
        assert self.chunking_manager.should_chunk_document(self.large_contract)
        
        # Find targets
        targets = self.chunking_manager.find_instruction_targets(instruction, self.large_contract)
        assert len(targets) > 0
        
        # Split document
        chunks = self.chunking_manager.split_document(self.large_contract)
        assert len(chunks) > 1
        
        # Prioritize chunks
        prioritized = self.chunking_manager.prioritize_chunks(chunks, targets)
        assert len(prioritized) == len(chunks)
        
        # Validate integrity
        assert self.chunking_manager.validate_chunk_integrity(chunks, prioritized)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])