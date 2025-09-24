"""
Contract Assistant vNext - PDF Utilities

Simple PDF handling utilities for Contract-Agent.
"""

import fitz  # PyMuPDF
import os
from typing import Optional, Union


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text content from PDF file using PyMuPDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content or None if failed
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        doc = fitz.open(file_path)
        text_content = ""
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text_content += page.get_text()
            text_content += "\n\n"  # Add page separation
        
        doc.close()
        return text_content.strip()
        
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return None


def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Extract text from various file formats.
    
    Args:
        file_path: Path to file
        
    Returns:
        Extracted text content or None if failed
    """
    if not os.path.exists(file_path):
        return None
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_ext in ['.txt', '.rtf']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            # Try to read as text file
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
                
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None


def save_rtf_content(content: str, output_path: str) -> bool:
    """
    Save RTF content to file.
    
    Args:
        content: RTF content to save
        output_path: Path to save RTF file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error saving RTF to {output_path}: {e}")
        return False
