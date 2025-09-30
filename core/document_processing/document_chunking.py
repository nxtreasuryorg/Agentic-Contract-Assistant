"""
Document Chunking Manager for Contract Assistant vNext

Based on nxtChat implementation with intelligent chunking and target prioritization.
Handles large contract documents by splitting them into manageable chunks with overlap
for context preservation.
"""

import re
import concurrent.futures
from typing import List, Tuple, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentChunkingManager:
    """
    Manages document chunking for large contract processing.
    
    Features:
    - Intelligent document splitting with configurable chunk size and overlap
    - Target section identification from user instructions
    - Chunk prioritization based on relevance to user instructions
    - Parallel chunk processing with rate limiting
    - Document reassembly with integrity validation
    """
    
    def __init__(self, chunk_size: int = 100000, chunk_overlap: int = 10000):
        """
        Initialize the DocumentChunkingManager.
        
        Args:
            chunk_size: Maximum size of each chunk in characters (default: 100,000)
            chunk_overlap: Overlap between chunks in characters (default: 10,000)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def should_chunk_document(self, document_content: str) -> bool:
        """
        Determine if document needs chunking based on size.
        
        Args:
            document_content: The document text to evaluate
            
        Returns:
            True if document should be chunked, False otherwise
        """
        return len(document_content) >= self.chunk_size
    
    def split_document(self, document_content: str) -> List[str]:
        """
        Split document into chunks using RecursiveCharacterTextSplitter.
        
        Args:
            document_content: The document text to split
            
        Returns:
            List of document chunks
        """
        if not self.should_chunk_document(document_content):
            return [document_content]
        
        chunks = self.text_splitter.split_text(document_content)
        print(f"Document split into {len(chunks)} chunks")
        return chunks
    
    def find_instruction_targets(self, instruction: str, document: str) -> List[str]:
        """
        Identify target sections from user instructions for chunk prioritization.
        
        Based on nxtChat implementation - extracts quoted text, action verbs,
        and common contract fields mentioned in the instruction.
        
        Args:
            instruction: User instruction/prompt
            document: Full document content
            
        Returns:
            List of target text sections found in the document
        """
        targets = []
        
        # Extract quoted text (likely direct references)
        quoted_text = re.findall(r'"([^"]*)"', instruction)
        quoted_text.extend(re.findall(r"'([^']*)'", instruction))
        
        # Process each quoted text segment
        for text in quoted_text:
            if len(text) > 3:
                # Look for case-insensitive matches
                text_lower = text.lower()
                doc_lower = document.lower()
                
                # Try to find all occurrences 
                start_pos = 0
                while start_pos < len(doc_lower):
                    found_pos = doc_lower.find(text_lower, start_pos)
                    if found_pos == -1:
                        break
                    
                    # Extract a context window around the match
                    context_start = max(0, found_pos - 100)
                    context_end = min(len(document), found_pos + len(text) + 200)
                    context = document[context_start:context_end]
                    targets.append(context)
                    
                    # Move to next position
                    start_pos = found_pos + len(text)
        
        # Split instruction into individual requests (common for multi-part instructions)
        instruction_parts = re.split(r'\n|\d+\.|\s*-\s*', instruction)
        
        # Process each instruction part
        for part in instruction_parts:
            part = part.strip()
            if len(part) < 5:  # Skip very short parts
                continue
                
            # Extract key verbs and subjects that indicate actions
            action_verbs = ["change", "modify", "replace", "update", "set", "remove", "delete", "add", "insert"]
            
            # Look for action verbs followed by potential targets
            for verb in action_verbs:
                if verb in part.lower():
                    verb_pos = part.lower().find(verb)
                    # Extract the target phrase (text after the verb)
                    if verb_pos >= 0 and verb_pos + len(verb) + 1 < len(part):
                        target_phrase = part[verb_pos + len(verb):].strip()
                        if len(target_phrase) > 3:
                            # Find this phrase in the document
                            # Use first few words for searching
                            search_terms = " ".join(target_phrase.split()[:3])
                            if len(search_terms) > 3:
                                # Look for the search terms in document
                                doc_lower = document.lower()
                                search_lower = search_terms.lower()
                                found_pos = doc_lower.find(search_lower)
                                if found_pos >= 0:
                                    # Extract context around match
                                    context_start = max(0, found_pos - 100)
                                    context_end = min(len(document), found_pos + len(search_terms) + 200)
                                    context = document[context_start:context_end]
                                    targets.append(context)
        
        # Look for common fields in contracts
        common_fields = [
            "effective date", "term", "termination", "governing law", "state", 
            "jurisdiction", "payment terms", "client", "provider", "customer",
            "representative", "fee", "price", "pricing", "deliverable", "party", "parties",
            "section", "article", "clause", "paragraph", "agreement", "contract"
        ]
        
        # Add any common fields mentioned in the instruction
        for field in common_fields:
            if field in instruction.lower():
                # Find this field in the document (could be multiple occurrences)
                field_lower = field.lower()
                doc_lower = document.lower()
                
                # Find all occurrences
                start_pos = 0
                while start_pos < len(doc_lower):
                    found_pos = doc_lower.find(field_lower, start_pos)
                    if found_pos == -1:
                        break
                    
                    # Extract a context window around the match
                    context_start = max(0, found_pos - 50)
                    context_end = min(len(document), found_pos + len(field) + 200)
                    context = document[context_start:context_end]
                    targets.append(context)
                    
                    # Move to next position
                    start_pos = found_pos + len(field)
        
        # Remove duplicates and near-duplicates
        unique_targets = []
        for target in targets:
            # Check if this target is too similar to existing ones
            is_duplicate = False
            for existing in unique_targets:
                # Simple overlap check
                if target in existing or existing in target:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_targets.append(target)
        
        print(f"Found {len(unique_targets)} unique target sections in document")
        return unique_targets
    
    def prioritize_chunks(self, chunks: List[str], targets: List[str]) -> List[str]:
        """
        Reorder chunks based on target relevance and importance.
        
        Based on nxtChat implementation - scores chunks based on target presence,
        position, and contract structure markers.
        
        Args:
            chunks: List of document chunks
            targets: List of target sections to prioritize
            
        Returns:
            Reordered list of chunks with most relevant first
        """
        if not targets:
            return chunks
        
        # Score each chunk based on target presence and relevance
        chunk_scores = []
        for i, chunk in enumerate(chunks):
            # Initialize score for this chunk
            score = 0
            chunk_lower = chunk.lower()
            
            # Score based on target presence
            for target in targets:
                target_lower = target.lower()
                
                # If target is fully contained in chunk, add higher score
                if target_lower in chunk_lower:
                    score += 5
                    
                    # Extra points if it's at the beginning or middle of the chunk (more likely to be complete)
                    target_pos = chunk_lower.find(target_lower)
                    if target_pos < len(chunk) // 3:  # In the first third
                        score += 2
                    elif target_pos < len(chunk) * 2 // 3:  # In the middle third
                        score += 1
                
                # If at least half of the target is in the chunk
                elif len(target_lower) > 10:
                    # Check for partial matches (first half or second half)
                    first_half = target_lower[:len(target_lower)//2]
                    second_half = target_lower[len(target_lower)//2:]
                    
                    if first_half in chunk_lower:
                        score += 2
                    if second_half in chunk_lower:
                        score += 2
            
            # Look for section headings/contract structure markers that might indicate important parts
            structure_markers = [
                "section", "article", "clause", "paragraph", 
                "parties", "agreement", "witnesseth", "whereas",
                "term", "termination", "payment", "services", "obligations",
                "governing law", "liability", "indemnification"
            ]
            
            # Add points for structure markers
            for marker in structure_markers:
                if marker in chunk_lower:
                    score += 1
            
            # Store score with chunk index
            chunk_scores.append((i, score))
        
        # Sort chunks by score (descending) and original order for equally scored chunks
        chunk_scores.sort(key=lambda x: (-x[1], x[0]))
        
        # Extract the reordering
        prioritized_indices = [i for i, _ in chunk_scores]
        
        # Create debug output to show the prioritization
        print("Chunk prioritization:")
        for idx, (orig_idx, score) in enumerate(chunk_scores):
            print(f"  Position {idx}: Chunk {orig_idx} (score: {score})")
        
        # Reorder chunks based on scores
        prioritized_chunks = [chunks[i] for i in prioritized_indices]
        
        return prioritized_chunks
    
    def process_chunks_parallel(
        self, 
        chunks: List[str], 
        instruction: str, 
        processor_func: callable,
        max_workers: int = 5
    ) -> List[Tuple[str, bool]]:
        """
        Process chunks in parallel with rate limiting.
        
        Args:
            chunks: List of document chunks to process
            instruction: User instruction for processing
            processor_func: Function to process each chunk (chunk, instruction, chunk_id) -> (result, changed)
            max_workers: Maximum number of concurrent workers (default: 5 for Bedrock rate limiting)
            
        Returns:
            List of tuples (processed_chunk, changed_flag) in original chunk order
        """
        processed_chunks = [None] * len(chunks)  # Pre-allocate result list
        total_chunks = len(chunks)
        
        # Define a worker function for parallel processing
        def process_chunk_worker(args):
            chunk, idx = args
            chunk_id = f"{idx+1}/{total_chunks}"  # Format as "current/total"
            try:
                result, changed = processor_func(chunk, instruction, chunk_id)
                return idx, result, changed
            except Exception as e:
                error_msg = str(e)
                print(f"Error processing chunk {chunk_id}: {error_msg}")
                
                # Check for credential errors
                if "AWS Credentials Error" in error_msg or "security token" in error_msg.lower():
                    # This is a critical error that won't resolve with retries
                    raise Exception(f"AWS Bedrock credentials error: {error_msg}")
                
                # For other errors, return original chunk
                return idx, chunk, False
        
        # Use parallel processing for chunks with ThreadPoolExecutor
        # Add rate limiting for Bedrock API
        max_workers = min(total_chunks, max_workers)
        print(f"Processing {total_chunks} chunks with {max_workers} workers")
        
        chunk_args = [(chunk, i) for i, chunk in enumerate(chunks)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_chunk_worker, arg): arg for arg in chunk_args}
            completed = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    idx, result, changed = future.result()
                    processed_chunks[idx] = (result, changed)
                    completed += 1
                    print(f"Completed chunk {completed}/{total_chunks}")
                    
                except Exception as e:
                    # Handle critical errors that should stop processing
                    if "AWS Bedrock credentials error" in str(e):
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        raise e
                    else:
                        print(f"Error in chunk processing: {e}")
        
        return processed_chunks
    
    def reassemble_chunks(self, processed_chunks: List[Tuple[str, bool]]) -> str:
        """
        Reassemble processed chunks into final document.
        
        Args:
            processed_chunks: List of tuples (processed_chunk, changed_flag)
            
        Returns:
            Final reassembled document
        """
        if not processed_chunks:
            return ""
        
        # Extract just the processed text from tuples
        chunks_text = []
        changes_detected = False
        
        for chunk_data in processed_chunks:
            if isinstance(chunk_data, tuple):
                chunk_text, changed = chunk_data
                chunks_text.append(chunk_text)
                if changed:
                    changes_detected = True
            else:
                # Handle case where chunk_data is just text
                chunks_text.append(str(chunk_data))
        
        # Simple concatenation for now - could be enhanced with overlap handling
        final_document = "".join(chunks_text)
        
        print(f"Reassembled document from {len(chunks_text)} chunks")
        if changes_detected:
            print("Changes detected during chunk processing")
        
        return final_document
    
    def validate_chunk_integrity(self, original_chunks: List[str], processed_chunks: List[str]) -> bool:
        """
        Validate that no content was lost during chunk processing.
        
        Args:
            original_chunks: Original document chunks
            processed_chunks: Processed document chunks
            
        Returns:
            True if integrity is maintained, False otherwise
        """
        if len(original_chunks) != len(processed_chunks):
            print(f"Chunk count mismatch: {len(original_chunks)} -> {len(processed_chunks)}")
            return False
        
        # Basic length comparison (processed chunks might be longer due to modifications)
        original_total_length = sum(len(chunk) for chunk in original_chunks)
        processed_total_length = sum(len(chunk) for chunk in processed_chunks)
        
        # Allow for reasonable size changes due to modifications
        size_change_ratio = abs(processed_total_length - original_total_length) / original_total_length
        if size_change_ratio > 0.5:  # More than 50% size change might indicate issues
            print(f"Significant size change detected: {size_change_ratio:.2%}")
            return False
        
        print("Chunk integrity validation passed")
        return True