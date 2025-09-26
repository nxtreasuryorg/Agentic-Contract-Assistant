#!/usr/bin/env python3
"""
Test Data Conversion Script
Converts all test data files to txt format with 1000 line limit
"""

import os
import sys
from pathlib import Path
import subprocess
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dependencies():
    """Install required dependencies for file conversion"""
    try:
        # Check if pdfplumber is available
        import pdfplumber
        logger.info("✅ pdfplumber is available")
    except ImportError:
        logger.info("Installing pdfplumber...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
        import pdfplumber
    
    try:
        # Check if python-docx is available
        import docx
        logger.info("✅ python-docx is available")
    except ImportError:
        logger.info("Installing python-docx...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
        import docx

def convert_pdf_to_txt(pdf_path: Path, output_path: Path, line_limit: int = 1000) -> bool:
    """Convert PDF to TXT with line limit"""
    try:
        import pdfplumber
        
        logger.info(f"Converting PDF: {pdf_path.name}")
        text_lines = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    # Split by lines and add to our collection
                    lines = page_text.split('\n')
                    text_lines.extend(lines)
                    
                # Check if we've reached our line limit
                if len(text_lines) >= line_limit:
                    text_lines = text_lines[:line_limit]
                    break
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in text_lines:
                f.write(line + '\n')
        
        logger.info(f"✅ Converted {pdf_path.name} -> {output_path.name} ({len(text_lines)} lines)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to convert {pdf_path.name}: {str(e)}")
        return False

def convert_docx_to_txt(docx_path: Path, output_path: Path, line_limit: int = 1000) -> bool:
    """Convert DOCX to TXT with line limit"""
    try:
        import docx
        
        logger.info(f"Converting DOCX: {docx_path.name}")
        doc = docx.Document(docx_path)
        text_lines = []
        
        for paragraph in doc.paragraphs:
            # Split paragraph text by lines if it contains line breaks
            para_lines = paragraph.text.split('\n')
            text_lines.extend(para_lines)
            
            # Check if we've reached our line limit
            if len(text_lines) >= line_limit:
                text_lines = text_lines[:line_limit]
                break
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in text_lines:
                f.write(line + '\n')
        
        logger.info(f"✅ Converted {docx_path.name} -> {output_path.name} ({len(text_lines)} lines)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to convert {docx_path.name}: {str(e)}")
        return False

def limit_txt_file(txt_path: Path, output_path: Path, line_limit: int = 1000) -> bool:
    """Limit existing TXT file to specified number of lines"""
    try:
        logger.info(f"Processing TXT: {txt_path.name}")
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Limit lines
        limited_lines = lines[:line_limit]
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(limited_lines)
        
        logger.info(f"✅ Limited {txt_path.name} -> {output_path.name} ({len(limited_lines)} lines, original: {len(lines)} lines)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to process {txt_path.name}: {str(e)}")
        return False

def convert_all_files(test_data_dir: Path, line_limit: int = 1000):
    """Convert all files in test data directory to txt format"""
    
    # Create converted directory
    converted_dir = test_data_dir / "converted"
    converted_dir.mkdir(exist_ok=True)
    
    logger.info(f"🚀 Starting conversion process in {test_data_dir}")
    logger.info(f"📝 Line limit: {line_limit}")
    logger.info(f"📁 Output directory: {converted_dir}")
    
    # Track conversion results
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    # Process all files in the directory
    for file_path in test_data_dir.iterdir():
        if not file_path.is_file():
            continue
            
        # Skip README and our conversion script
        if file_path.name in ['README.md', 'convert_to_txt.py']:
            results['skipped'].append(file_path.name)
            continue
        
        # Determine output filename
        output_name = file_path.stem + '_converted.txt'
        output_path = converted_dir / output_name
        
        # Convert based on file extension
        success = False
        if file_path.suffix.lower() == '.pdf':
            success = convert_pdf_to_txt(file_path, output_path, line_limit)
        elif file_path.suffix.lower() == '.docx':
            success = convert_docx_to_txt(file_path, output_path, line_limit)
        elif file_path.suffix.lower() == '.txt':
            success = limit_txt_file(file_path, output_path, line_limit)
        else:
            logger.warning(f"⚠️ Unsupported file type: {file_path.name}")
            results['skipped'].append(file_path.name)
            continue
        
        if success:
            results['success'].append(file_path.name)
        else:
            results['failed'].append(file_path.name)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("📊 CONVERSION SUMMARY")
    logger.info("="*60)
    logger.info(f"✅ Successfully converted: {len(results['success'])}")
    for file in results['success']:
        logger.info(f"   - {file}")
    
    if results['failed']:
        logger.info(f"❌ Failed conversions: {len(results['failed'])}")
        for file in results['failed']:
            logger.info(f"   - {file}")
    
    if results['skipped']:
        logger.info(f"⏭️ Skipped files: {len(results['skipped'])}")
        for file in results['skipped']:
            logger.info(f"   - {file}")
    
    logger.info("="*60)
    logger.info(f"🎯 Total files processed: {len(results['success']) + len(results['failed'])}")
    logger.info(f"📁 Converted files location: {converted_dir}")
    
    return results

if __name__ == "__main__":
    # Set up dependencies
    setup_dependencies()
    
    # Get the current directory (should be test_data)
    current_dir = Path(__file__).parent
    
    # Run conversion with 1000 line limit
    results = convert_all_files(current_dir, line_limit=1000)
    
    # Exit with error code if any conversions failed
    if results['failed']:
        sys.exit(1)
    else:
        logger.info("✅ All conversions completed successfully!")
        sys.exit(0)
