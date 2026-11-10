# Extraction evaluation (2026-11-10, model `openai/gpt-oss-120b`)

10 documents, 10 fields each.

| Field | json |
|---|---|
| customer_name | 100% |
| product_name | 100% |
| product_strength | 90% |
| batch_number | 100% |
| manufacturing_date | 100% |
| expiry_date | 100% |
| quantity_affected | 100% |
| complaint_date | 100% |
| complaint_type | 90% |
| initial_severity | 90% |
| **Overall accuracy** | **97%** |
| **Hallucination rate** | **0%** |
| **Risk level agrees** | **90%** |

Hallucination rate = of the fields NOT in the document, how often the model filled one in.

## Every miss

### json
- `sample3.pdf` product_strength: **missed** (got `None`)
- `05_informal_chat.txt` complaint_type: **wrong** (got `Packaging`)
- `05_informal_chat.txt` initial_severity: **wrong** (got `Minor`)
