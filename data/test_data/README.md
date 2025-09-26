# Legal Contract Testing Samples - 10 Sample Set

## Overview
This folder contains 10 legal contract samples selected for testing the Contract Assistant vNext system. These samples are designed to test various aspects of the system including counterparty modifications, legal domicile shifts, blame attribution changes, clause additions/deletions, and entity changes.

## Sample Descriptions

### PDF Samples (Contract Assistant Core Testing)

**sample_01.pdf** (2.86 KB)
- Source: Original sample 1
- Type: Small legal document 
- Use: Basic PDF processing and RTF conversion testing

**sample_02.pdf** (118.08 KB)  
- Source: Original sample 2
- Type: Medium-sized legal contract
- Use: Standard contract manipulation testing

**sample_03.pdf** (265.04 KB)
- Source: GpaqAcquisitionHoldingsInc_20200123_S-4A_EX-10.8_11951679_EX-10.8_Service Agreement.pdf
- Type: Corporate acquisition service agreement
- Use: Complex corporate entity testing, counterparty modification testing

**sample_04.pdf** (733.76 KB)
- Source: legal agreement 1.pdf  
- Type: Comprehensive financial services agreement
- Use: Large document chunking testing (>25,000 character threshold), blame attribution testing

**sample_05.pdf** (358.91 KB)
- Source: legal agreement 2.pdf
- Type: Multi-party legal agreement
- Use: Legal domicile shift testing, multi-party contract analysis

### Text Format Samples (Alternative Format Testing)

**sample_06.txt** (76.52 KB)
- Source: legal-agreement 1.txt
- Type: Financial services agreement (text format)
- Use: Text-to-RTF conversion testing, comprehensive contract analysis

**sample_07.txt** (48.09 KB) 
- Source: legal-agreement 2.txt
- Type: Cryptocurrency/blockchain trading agreement
- Use: Modern digital asset contract testing, risk disclaimer analysis

**sample_09.txt** (35.24 KB)
- Source: First half of legal-agreement 1.txt (lines 1-250)
- Type: Financial services agreement - Part 1 (Sections 1-10)
- Use: Partial document processing, contract section analysis

**sample_10.txt** (41.33 KB)
- Source: Second half of legal-agreement 1.txt (lines 251-508)
- Type: Financial services agreement - Part 2 (Schedules & DPA)
- Use: Data processing agreement testing, schedule manipulation

### DOCX Sample (Office Format Testing)

**sample_08.docx** (31.84 KB)
- Source: legal agreement 2.docx
- Type: Legal agreement in Word format
- Use: DOCX-to-RTF conversion testing, Office document compatibility

## Testing Coverage

These samples provide comprehensive coverage for:

1. **Document Format Variety**: PDF, TXT, DOCX formats
2. **Size Range**: From 2.86 KB to 733.76 KB (testing chunking thresholds)
3. **Contract Types**: 
   - Financial services agreements
   - Corporate acquisition agreements  
   - Service agreements
   - Cryptocurrency trading agreements
   - Data processing agreements
4. **Complexity Levels**: Simple to complex multi-party contracts
5. **Entity Testing**: Various corporate structures and counterparties
6. **Legal Concepts**: Blame attribution, domicile, counterparty relationships

## Usage Notes

- All samples are ready for the Contract Assistant vNext actor-critic pipeline
- Larger documents (sample_04, sample_05) will test the 25,000+ character chunking system
- Text samples can test alternative input format handling
- Split samples (09-10) can test partial document reconstruction
- All samples contain realistic legal language suitable for semantic manipulation testing

## File Naming Convention

Files are named `sample_XX.ext` where:
- XX = Sequential number 01-10
- ext = Original file extension (pdf, txt, docx)
