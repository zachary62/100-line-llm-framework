"""Helper: generate a sample invoice PDF for invoice_processing.py"""
from fpdf import FPDF
import os

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=False)

# Header
pdf.set_font("Helvetica", "B", 20)
pdf.cell(0, 12, "INVOICE", align="R", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 6, "#INV-2024-0892", align="R", new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)

# From / To
pdf.set_font("Helvetica", "B", 10)
pdf.cell(95, 6, "From:", new_x="RIGHT")
pdf.cell(95, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
for from_line, to_line in [
    ("TechSupply Co.", "Acme Analytics"),
    ("123 Industrial Ave", "456 Market St"),
    ("San Jose, CA 95134", "San Francisco, CA 94105"),
    ("Tax ID: 87-1234567", ""),
]:
    pdf.cell(95, 5, from_line, new_x="RIGHT")
    pdf.cell(95, 5, to_line, new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)

# Dates
pdf.set_font("Helvetica", "", 10)
pdf.cell(95, 5, "Date: March 15, 2024", new_x="RIGHT")
pdf.cell(95, 5, "Due: April 14, 2024", new_x="LMARGIN", new_y="NEXT")
pdf.cell(95, 5, "Terms: Net 30", new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)

# Table header
pdf.set_font("Helvetica", "B", 10)
pdf.set_fill_color(230, 230, 230)
pdf.cell(80, 8, "Item", border=1, fill=True)
pdf.cell(20, 8, "Qty", border=1, fill=True, align="C")
pdf.cell(40, 8, "Unit Price", border=1, fill=True, align="R")
pdf.cell(40, 8, "Amount", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

# Table rows
pdf.set_font("Helvetica", "", 10)
items = [
    ("GPU Server (A100 80GB)", "2", "$12,499.00", "$24,998.00"),
    ("NVMe SSD 2TB", "4", "$289.99", "$1,159.96"),
    ("Server Rack Mount Kit", "2", "$74.50", "$149.00"),
    ("Setup & Configuration", "1", "$1,500.00", "$1,500.00"),
]
for item, qty, price, amount in items:
    pdf.cell(80, 7, item, border=1)
    pdf.cell(20, 7, qty, border=1, align="C")
    pdf.cell(40, 7, price, border=1, align="R")
    pdf.cell(40, 7, amount, border=1, align="R", new_x="LMARGIN", new_y="NEXT")

# Totals
pdf.ln(4)
pdf.set_font("Helvetica", "", 10)
pdf.cell(140, 6, "Subtotal:", align="R")
pdf.cell(40, 6, "$27,806.96", align="R", new_x="LMARGIN", new_y="NEXT")
pdf.cell(140, 6, "Tax (8.75%):", align="R")
pdf.cell(40, 6, "$2,433.11", align="R", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 11)
pdf.cell(140, 7, "Total:", align="R")
pdf.cell(40, 7, "$30,240.07", align="R", new_x="LMARGIN", new_y="NEXT")

# Notes
pdf.ln(10)
pdf.set_font("Helvetica", "I", 9)
pdf.cell(0, 5, "Notes: Rush delivery requested. 2-year warranty included on all hardware.")

out = os.path.join(os.path.dirname(__file__), "invoice.pdf")
pdf.output(out)
print(f"Created {out}")
