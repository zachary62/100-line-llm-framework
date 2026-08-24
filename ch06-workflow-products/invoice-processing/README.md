# Invoice processing: PDF in, structured data out

Section 6.5. A multimodal model extracts the fields, then plain arithmetic validates them — line items sum to the subtotal, tax math checks out, subtotal plus tax equals the total. Design in [docs/design.md](docs/design.md).

```mermaid
flowchart LR
    extract[ExtractFields] --> validate[Validate]
```

```bash
python create_invoice_pdf.py   # once, to generate the sample invoice.pdf
python main.py
```

## Sample output

```
  Extracted 4 line items from PDF
  Validation passed

Invoice: #INV-2024-0892
Vendor: TechSupply Co. -> Customer: Acme Analytics
Items: 4
  2x GPU Server (A100 80GB): $24998.00
  4x NVMe SSD 2TB: $1159.96
  2x Server Rack Mount Kit: $149.00
  1x Setup & Configuration: $1500.00
Total: $30240.07 (due April 14, 2024)
```
