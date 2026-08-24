import sys, os, pathlib, yaml
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from pocketflow import Node
from call_llm import client, FAST_MODEL
from google.genai import types

class ExtractFields(Node):
    def prep(self, shared):
        return shared["pdf_path"]
    def exec(self, pdf_path):
        pdf_bytes = pathlib.Path(pdf_path).read_bytes()
        prompt = """Extract fields from this invoice PDF. Output ONLY yaml:
```yaml
invoice_number: "..."
vendor: "..."
vendor_tax_id: "..."
customer: "..."
date: "..."
due_date: "..."
line_items:
  - description: "..."
    quantity: 1
    unit_price: 0.00
    amount: 0.00
subtotal: 0.00
tax_rate: 0.0
tax_amount: 0.00
total: 0.00
notes: "..."
```"""
        resp = client.models.generate_content(
            model=FAST_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )
        yaml_str = resp.text.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)
    def post(self, shared, prep_res, exec_res):
        shared["extracted"] = exec_res
        print(f"  Extracted {len(exec_res.get('line_items', []))} line items from PDF")

class Validate(Node):
    def prep(self, shared):
        return shared["extracted"]
    def exec(self, data):
        errors = []
        items = data.get("line_items", [])
        computed_subtotal = sum(item["amount"] for item in items)
        if abs(computed_subtotal - data["subtotal"]) > 0.01:
            errors.append(f"Subtotal mismatch: items sum to ${computed_subtotal:.2f}, invoice says ${data['subtotal']:.2f}")

        tax_pct = data["tax_rate"] if data["tax_rate"] > 1 else data["tax_rate"] * 100
        computed_tax = round(data["subtotal"] * tax_pct / 100, 2)
        if abs(computed_tax - data["tax_amount"]) > 0.01:
            errors.append(f"Tax mismatch: {tax_pct}% of ${data['subtotal']:.2f} = ${computed_tax:.2f}, invoice says ${data['tax_amount']:.2f}")

        computed_total = data["subtotal"] + data["tax_amount"]
        if abs(computed_total - data["total"]) > 0.01:
            errors.append(f"Total mismatch: ${data['subtotal']:.2f} + ${data['tax_amount']:.2f} = ${computed_total:.2f}, invoice says ${data['total']:.2f}")

        for item in items:
            expected = round(item["quantity"] * item["unit_price"], 2)
            if abs(expected - item["amount"]) > 0.01:
                errors.append(f"Line item '{item['description']}': {item['quantity']} x ${item['unit_price']:.2f} = ${expected:.2f}, says ${item['amount']:.2f}")
        return errors

    def post(self, shared, prep_res, exec_res):
        shared["validation_errors"] = exec_res
        if exec_res:
            print(f"  Validation FAILED: {exec_res}")
        else:
            print("  Validation passed")
