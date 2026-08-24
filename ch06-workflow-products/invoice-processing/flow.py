from pocketflow import Flow
from nodes import ExtractFields, Validate

def create_invoice_flow():
    extract = ExtractFields()
    validate = Validate()

    extract >> validate
    return Flow(start=extract)
