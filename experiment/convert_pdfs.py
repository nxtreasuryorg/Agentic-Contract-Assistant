#!/usr/bin/env python3
"""
Convert PDF files from data/ to RTF format for experiments.

This script extracts text from PDFs and wraps it in minimal RTF format
for use with the actor-critic evaluation system.
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF not installed. Install with: pip install PyMuPDF")
    sys.exit(1)


def text_to_rtf(text: str) -> str:
    """
    Convert plain text to RTF format with proper escaping.
    
    Args:
        text: Plain text content
        
    Returns:
        RTF formatted content
    """
    # RTF escape sequences
    escaped = text.replace("\\", "\\\\")
    escaped = escaped.replace("{", "\\{")
    escaped = escaped.replace("}", "\\}")
    
    # Convert newlines to RTF paragraphs
    lines = escaped.split("\n")
    rtf_body = "\\par\n".join(lines)
    
    # Wrap in RTF document structure
    rtf_document = (
        "{\\rtf1\\ansi\\deff0\n"
        "{\\fonttbl{\\f0 Times New Roman;}}\n"
        "\\f0\\fs24\n"
        f"{rtf_body}\n"
        "}"
    )
    
    return rtf_document


def convert_pdf_to_rtf(pdf_path: Path, rtf_path: Path) -> bool:
    """
    Convert a PDF file to RTF format.
    
    Args:
        pdf_path: Path to input PDF file
        rtf_path: Path to output RTF file
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Converting {pdf_path.name} to RTF...")
    
    # Extract text from PDF using PyMuPDF
    try:
        doc = fitz.open(str(pdf_path))
        text_content = ""
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text_content += page.get_text()
            text_content += "\n\n"  # Add page separation
        
        doc.close()
        text = text_content.strip()
        
        if not text:
            print(f"  ❌ No text extracted from {pdf_path.name}")
            return False
            
    except Exception as e:
        print(f"  ❌ Failed to extract text from {pdf_path.name}: {e}")
        return False
    
    # Convert to RTF
    rtf_content = text_to_rtf(text)
    
    # Ensure output directory exists
    rtf_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write RTF file
    try:
        with open(rtf_path, 'w', encoding='utf-8') as f:
            f.write(rtf_content)
        print(f"  ✅ Created {rtf_path.relative_to(Path.cwd())}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to write {rtf_path.name}: {e}")
        return False


def main():
    """Convert all PDFs in data/ folder to RTF format."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    output_dir = script_dir / "converted" / "rtf"
    
    print("=" * 60)
    print("PDF to RTF Conversion for Actor-Critic Experiments")
    print("=" * 60)
    print()
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return 1
    
    # Find all PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {data_dir}")
        return 1
    
    print(f"Found {len(pdf_files)} PDF file(s) to convert:\n")
    
    # Convert each PDF
    success_count = 0
    for pdf_path in sorted(pdf_files):
        # Generate output filename
        rtf_filename = pdf_path.stem + ".rtf"
        rtf_path = output_dir / rtf_filename
        
        if convert_pdf_to_rtf(pdf_path, rtf_path):
            success_count += 1
        print()
    
    # Summary
    print("=" * 60)
    print(f"Conversion complete: {success_count}/{len(pdf_files)} successful")
    print("=" * 60)
    print()
    
    if success_count > 0:
        print("📁 RTF files created in: converted/rtf/")
        print("\n📝 Next steps:")
        print("   1. Update config/config.yaml to reference the correct RTF filenames")
        print("   2. Run experiments using: python runners/evaluate.py --document <key> --scenario <file>")
    
    return 0 if success_count == len(pdf_files) else 1


if __name__ == "__main__":
    sys.exit(main())
