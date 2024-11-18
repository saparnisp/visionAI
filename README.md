# Vision AI Invoice Data Extractor

This project uses Vision AI to automatically extract structured data from PDF invoices. It converts PDF invoices to images and uses the Llama 3.2 Vision model to extract key information such as invoice numbers, dates, amounts, and supplier/receiver details.

## Features

- PDF to image conversion using PyMuPDF
- Vision AI-powered data extraction
- Structured JSON output
- Batch processing of multiple invoices
- Detailed error handling and logging

## Requirements

- Python 3.x
- Ollama with llama3.2-vision model running locally
- Required Python packages:
  - PyMuPDF (fitz)
  - Pillow
  - requests

## Installation

1. Clone the repository:
```bash
git clone https://github.com/saparnisp/visionAI.git
cd visionAI
```

2. Install required packages:
```bash
pip install PyMuPDF Pillow requests
```

3. Ensure Ollama is running with llama3.2-vision model on localhost:11434

## Usage

### Process Multiple Invoices

Place your PDF invoices in the `invoices` directory and run:

```bash
python process_invoices.py
```

This will process all PDF files in the invoices directory and save the extracted data to `extracted_invoices.json`.

### Process Single Invoice

To test with a single invoice:

```bash
python test_single_invoice.py
```

## Output Format

The extracted data is saved in JSON format with the following structure:

```json
{
    "document": {
        "invoice_id": "string",
        "invoice_date": "YYYY-MM-DD",
        "total_amount": number,
        "net_amount": number,
        "tax_percentage": number,
        "total_tax_amount": number,
        "supplier_name": "string",
        "supplier_address": "string",
        "supplier_tax_id": "string",
        "supplier_registration": "string",
        "receiver_name": "string",
        "receiver_address": "string",
        "receiver_tax_id": "string",
        "receiver_registration": "string",
        "line_items": [
            {
                "amount": number,
                "description": "string"
            }
        ],
        "status": "string",
        "file_name": "string",
        "file_path": "string",
        "file_size": "string",
        "mime_type": "string",
        "upload_date": "ISO datetime"
    }
}
```

## Project Structure

- `process_invoices.py`: Main script for batch processing invoices
- `test_single_invoice.py`: Script for testing single invoice processing
- `invoices/`: Directory containing PDF invoices to process
- `extracted_invoices.json`: Output file containing extracted data

## Error Handling

The system includes robust error handling for:
- PDF conversion issues
- Vision AI processing errors
- JSON parsing and formatting
- File I/O operations

Each error is logged with detailed information to help diagnose and resolve issues.
