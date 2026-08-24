"""Section 6.5: Invoice Processing — PDF in, structured data out.

Run create_invoice_pdf.py first to generate the sample invoice.pdf.
"""
import os
from flow import create_invoice_flow

INVOICE_PDF = os.path.join(os.path.dirname(__file__), "invoice.pdf")

shared = {"pdf_path": INVOICE_PDF}
create_invoice_flow().run(shared)

data = shared["extracted"]
print(f"\nInvoice: {data['invoice_number']}")
print(f"Vendor: {data['vendor']} -> Customer: {data['customer']}")
print(f"Items: {len(data['line_items'])}")
for item in data["line_items"]:
    print(f"  {item['quantity']}x {item['description']}: ${item['amount']:.2f}")
print(f"Total: ${data['total']:.2f} (due {data['due_date']})")
