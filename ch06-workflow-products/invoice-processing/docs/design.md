# Design Doc: Invoice Processing

> Please DON'T remove notes for AI

## Requirements

> Notes for AI: Keep it simple and clear.
> If the requirements are abstract, write concrete user stories

An accounts team drops in an invoice PDF and gets back structured fields: invoice number, vendor, line items, totals. Extraction alone isn't enough — the model can misread a number with total confidence, so every extracted invoice is re-checked with plain arithmetic (line items sum to the subtotal, tax math checks out, subtotal plus tax equals the total) before anything downstream trusts it.

## Flow Design

> Notes for AI:
> 1. Consider the design patterns of agent, map-reduce, rag, and workflow. Apply them if they fit.
> 2. Present a concise, high-level description of the workflow.

### Applicable Design Pattern:

**Workflow** — a two-node chain: an LLM extraction stage followed by a deterministic validation stage with no LLM at all. The cheap check catches the expensive mistake.

### Flow high-level Design:

1. **ExtractFields**: Sends the PDF bytes plus a YAML schema prompt to a multimodal model and parses the structured result.
2. **Validate**: Pure Python arithmetic over the extracted numbers; collects every mismatch as an error.

```mermaid
flowchart LR
    extract[ExtractFields] --> validate[Validate]
```

## Utility Functions

> Notes for AI:
> 1. Understand the utility function definition thoroughly by reviewing the doc.
> 2. Include only the necessary utility functions, based on nodes in the flow.

1. **Multimodal LLM client** (`call_llm.py` at the repo root — `client` and `FAST_MODEL`)
   - *Input*: PDF bytes + prompt
   - *Output*: YAML text
   - Used by ExtractFields. Validate needs no utilities.

2. **Sample invoice generator** (`create_invoice_pdf.py`)
   - Writes `invoice.pdf` with fpdf2 so the example runs without any real invoice.

## Node Design

### Shared Store

> Notes for AI: Try to minimize data redundancy

```python
shared = {
    "pdf_path": "invoice.pdf",   # Input
    "extracted": {},             # ExtractFields output: parsed invoice fields
    "validation_errors": [],     # Validate output: empty list means clean
}
```

### Node Steps

> Notes for AI: Carefully decide whether to use Batch/Async Node/Flow.

1. **ExtractFields** — Regular. *prep*: read "pdf_path". *exec*: send PDF bytes and the YAML schema to the multimodal model, parse the YAML. *post*: write "extracted".
2. **Validate** — Regular, no LLM. *prep*: read "extracted". *exec*: recompute subtotal, tax, total, and each line item; collect mismatches. *post*: write "validation_errors".
