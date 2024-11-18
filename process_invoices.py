import os
import json
import base64
import requests
from datetime import datetime, UTC
import fitz  # PyMuPDF
from PIL import Image
import io
import re

def extract_markdown_data(markdown_text):
    """Extract structured data from markdown formatted text"""
    try:
        # Initialize the data structure
        data = {
            "invoice_id": None,
            "invoice_date": None,
            "total_amount": None,
            "net_amount": None,
            "tax_percentage": None,
            "total_tax_amount": None,
            "supplier_name": None,
            "supplier_address": None,
            "supplier_tax_id": None,
            "supplier_registration": None,
            "receiver_name": None,
            "receiver_address": None,
            "receiver_tax_id": None,
            "receiver_registration": None,
            "line_items": []
        }
        
        # Extract invoice ID
        match = re.search(r'Invoice ID:\s*(\d+)', markdown_text)
        if match:
            data["invoice_id"] = match.group(1).strip()
        
        # Extract date
        match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', markdown_text)
        if match:
            data["invoice_date"] = match.group(1).strip()
        
        # Extract amounts
        total_match = re.search(r'Total Amount:\s*(\d+\.?\d*)\s*EUR', markdown_text)
        if total_match:
            data["total_amount"] = float(total_match.group(1))
        
        net_match = re.search(r'Net Amount:\s*(\d+\.?\d*)\s*EUR', markdown_text)
        if net_match:
            data["net_amount"] = float(net_match.group(1))
        
        tax_match = re.search(r'Tax Percentage:\s*(\d+)%', markdown_text)
        if tax_match:
            data["tax_percentage"] = float(tax_match.group(1))
        
        tax_amount_match = re.search(r'Tax Amount:\s*(\d+\.?\d*)\s*EUR', markdown_text)
        if tax_amount_match:
            data["total_tax_amount"] = float(tax_amount_match.group(1))
        
        # Extract supplier information
        supplier_section = re.search(r"supplier's details.*?:(.*?)(?=The|$)", markdown_text, re.DOTALL | re.IGNORECASE)
        if supplier_section:
            supplier_text = supplier_section.group(1)
            
            name_match = re.search(r'Name:\s*([^\n]+)', supplier_text)
            if name_match:
                data["supplier_name"] = name_match.group(1).strip()
            
            address_match = re.search(r'Address:\s*([^\n]+)', supplier_text)
            if address_match:
                data["supplier_address"] = address_match.group(1).strip()
            
            tax_id_match = re.search(r'Tax ID:\s*([^\n]+)', supplier_text)
            if tax_id_match:
                data["supplier_tax_id"] = tax_id_match.group(1).strip()
            
            reg_match = re.search(r'Registration Number:\s*([^\n]+)', supplier_text)
            if reg_match:
                data["supplier_registration"] = reg_match.group(1).strip()
        
        # Extract line items
        line_items_section = re.search(r'line item.*?:.*?Amount:\s*(\d+\.?\d*)\s*EUR.*?Description:\s*([^\n]+)', markdown_text, re.DOTALL | re.IGNORECASE)
        if line_items_section:
            amount = float(line_items_section.group(1))
            description = line_items_section.group(2).strip()
            data["line_items"].append({
                "amount": amount,
                "description": description
            })
        
        return data
    except Exception as e:
        print(f"Error parsing markdown: {str(e)}")
        return None

def fix_json_string(json_str):
    """Fix common JSON formatting issues"""
    try:
        # First try to parse it as is
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # Find the JSON object in the text
            match = re.search(r'\{[\s\S]*\}', json_str)
            if match:
                json_str = match.group(0)
                
                # Replace empty string values with null
                json_str = re.sub(r':\s*""', ': null', json_str)
                
                # Add commas between key-value pairs
                json_str = re.sub(r'"\s+(?=")', '",\n    ', json_str)
                
                # Add commas between array items
                json_str = re.sub(r'}\s+{', '},\n        {', json_str)
                
                # Clean up any remaining formatting issues
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                
                print("\nCleaned JSON:")
                print(json_str)
                
                return json.loads(json_str)
            else:
                # Try to parse as markdown if JSON object not found
                return extract_markdown_data(json_str)
        except json.JSONDecodeError as e:
            print(f"Failed to fix JSON: {str(e)}")
            print("Attempted to fix JSON:")
            print(json_str)
            return None

def convert_pdf_to_image(pdf_path, page_num=0):
    """Convert a PDF page to a base64 encoded image"""
    try:
        # Handle special characters in filename
        if not os.path.exists(pdf_path):
            # Try to find the file with normalized name
            dir_path = os.path.dirname(pdf_path)
            base_name = os.path.basename(pdf_path)
            for file in os.listdir(dir_path):
                if file.lower() == base_name.lower():
                    pdf_path = os.path.join(dir_path, file)
                    break
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        # Get the page's pixmap (image)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Scale up for better quality
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert to JPEG format in memory
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        # Convert to base64
        return base64.b64encode(img_byte_arr).decode()
    except Exception as e:
        print(f"Error converting PDF to image: {str(e)}")
        return None

def extract_invoice_data(image_base64, pdf_path):
    """Extract data from invoice image using Ollama vision model"""
    url = "http://localhost:11434/api/chat"
    
    prompt = """Analyze this invoice image and extract the following information in a valid JSON format with proper commas between fields:
    {
        "invoice_id": "string - invoice number or identifier",
        "invoice_date": "string - date of invoice (YYYY-MM-DD)",
        "total_amount": number - total amount including tax,
        "net_amount": number - amount before tax,
        "tax_percentage": number - VAT percentage,
        "total_tax_amount": number - total tax amount,
        "supplier_name": "string - company issuing invoice",
        "supplier_address": "string - address of supplier",
        "supplier_tax_id": "string - tax ID/VAT number",
        "supplier_registration": "string - company registration number",
        "receiver_name": "string - receiving company/person",
        "receiver_address": "string - address of receiver",
        "receiver_tax_id": "string - tax ID of receiver",
        "receiver_registration": "string - registration number of receiver",
        "line_items": [
            {
                "amount": number - item amount,
                "description": "string - item description"
            }
        ]
    }
    
    IMPORTANT: Format the response as a proper JSON object with commas after each key-value pair. Use null for missing values instead of empty strings. Return ONLY the JSON object, no other text."""
    
    payload = {
        "model": "llama3.2-vision",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in extracting structured data from invoice images. Always return data in valid JSON format with proper commas between fields. Use null for missing values instead of empty strings."
            },
            {
                "role": "user",
                "content": prompt,
                "images": [image_base64]
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "message" in result and "content" in result["message"]:
            # Try to fix and parse the JSON from the response content
            content = result["message"]["content"]
            print("\nRaw response content:")
            print(content)
            
            extracted_data = fix_json_string(content)
            if extracted_data:
                # Add metadata
                final_result = {
                    "document": {
                        **extracted_data,
                        "status": "Done",
                        "file_name": os.path.basename(pdf_path),
                        "file_path": pdf_path,
                        "file_size": str(os.path.getsize(pdf_path)),
                        "mime_type": "application/pdf",
                        "document_id": None,
                        "upload_date": datetime.now(UTC).isoformat()
                    }
                }
                
                # Convert the result to string and back to ensure proper JSON formatting
                return json.loads(json.dumps(final_result))
            else:
                return {
                    "error": "Failed to parse or fix JSON response",
                    "raw_response": content
                }
        else:
            return {
                "error": "Unexpected response format",
                "raw_response": result
            }
            
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def process_invoices(directory):
    """Process all PDF files in the specified directory"""
    results = []
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    
    for filename in pdf_files:
        pdf_path = os.path.join(directory, filename)
        print(f"\nProcessing {filename}...")
        
        # Convert PDF to image
        image_base64 = convert_pdf_to_image(pdf_path)
        if not image_base64:
            results.append({
                "error": f"Failed to convert PDF to image: {filename}"
            })
            continue
        
        # Extract data from image
        result = extract_invoice_data(image_base64, pdf_path)
        results.append(result)
        
        # Save intermediate results
        with open("extracted_invoices.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Completed processing {filename}")
    
    return results

if __name__ == "__main__":
    invoices_dir = "invoices"
    print(f"Starting to process invoices in {invoices_dir}...")
    
    results = process_invoices(invoices_dir)
    
    # Save final results
    output_file = "extracted_invoices.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nProcessing complete. Results saved to {output_file}")
