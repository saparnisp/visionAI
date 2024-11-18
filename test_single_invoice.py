from process_invoices import convert_pdf_to_image, extract_invoice_data

def test_single_invoice():
    # Test with the example invoice from your initial JSON
    pdf_path = "invoices/saskaita_208930951_20240131.pdf"
    print(f"\nProcessing {pdf_path}...")
    
    # Convert PDF to image
    print("Converting PDF to image...")
    image_base64 = convert_pdf_to_image(pdf_path)
    if not image_base64:
        print("Failed to convert PDF to image")
        return
    
    print(f"Successfully converted PDF to image (base64 size: {len(image_base64)} bytes)")
    
    # Extract data from image
    print("\nExtracting data from image...")
    result = extract_invoice_data(image_base64, pdf_path)
    
    # Save result
    import json
    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\nResult:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\nTest complete. Results saved to test_result.json")

if __name__ == "__main__":
    test_single_invoice()
