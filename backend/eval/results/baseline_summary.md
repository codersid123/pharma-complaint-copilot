# Extraction evaluation (2026-11-10, model `openai/gpt-oss-120b`)

10 documents, 10 fields each.

| Field | json | structured |
|---|---|---|
| customer_name | 50% | 30% |
| product_name | 100% | 40% |
| product_strength | 90% | 50% |
| batch_number | 100% | 60% |
| manufacturing_date | 100% | 70% |
| expiry_date | 100% | 80% |
| quantity_affected | 100% | 50% |
| complaint_date | 90% | 50% |
| complaint_type | 80% | 50% |
| initial_severity | 80% | 40% |
| **Overall accuracy** | **89%** | **52%** |
| **Hallucination rate** | **0%** | **0%** |
| **Risk level agrees** | **80%** | **40%** |

Hallucination rate = of the fields NOT in the document, how often the model filled one in.

## Every miss

### json
- `sample2.pdf` customer_name: **wrong** (got `Priya`)
- `sample2.pdf` complaint_type: **wrong** (got `Packaging`)
- `sample3.pdf` product_strength: **missed** (got `None`)
- `04_formal_letter.txt` customer_name: **wrong** (got `Dr. Anjali Nair`)
- `04_formal_letter.txt` initial_severity: **wrong** (got `Minor`)
- `05_informal_chat.txt` customer_name: **wrong** (got `Ravi`)
- `05_informal_chat.txt` complaint_type: **wrong** (got `Packaging`)
- `05_informal_chat.txt` initial_severity: **wrong** (got `Minor`)
- `06_adverse_event.eml` customer_name: **wrong** (got `Dr. S. Iyer`)
- `06_adverse_event.eml` complaint_date: **wrong** (got `2026-09-03`)
- `08_phone_transcript.txt` customer_name: **wrong** (got `Arjun Shah`)

### structured
- `sample2.pdf`: **error** BadRequestError: Error code: 400 - {'error': {'message': 'Tool choice is required, but model did not call a tool', 'type': 'invalid_request_error', 'code': 'tool_use_failed', 'failed_generation': '{\n  "complaint_source": "Email",\n  "customer_name": "Priya",\n  "product_name": "Metformin",\n  "prod
- `sample2.pdf` customer_name: **missed** (got `None`)
- `sample2.pdf` product_name: **missed** (got `None`)
- `sample2.pdf` product_strength: **missed** (got `None`)
- `sample2.pdf` quantity_affected: **missed** (got `None`)
- `sample2.pdf` complaint_type: **missed** (got `None`)
- `sample2.pdf` initial_severity: **missed** (got `None`)
- `sample3.pdf`: **error** BadRequestError: Error code: 400 - {'error': {'message': 'Tool choice is required, but model did not call a tool', 'type': 'invalid_request_error', 'code': 'tool_use_failed', 'failed_generation': '{\n  "complaint_source": "Customer",\n  "customer_name": "Aurora Pharma Formulations Ltd (API customer)
- `sample3.pdf` customer_name: **missed** (got `None`)
- `sample3.pdf` product_name: **missed** (got `None`)
- `sample3.pdf` product_strength: **missed** (got `None`)
- `sample3.pdf` batch_number: **missed** (got `None`)
- `sample3.pdf` manufacturing_date: **missed** (got `None`)
- `sample3.pdf` quantity_affected: **missed** (got `None`)
- `sample3.pdf` complaint_date: **missed** (got `None`)
- `sample3.pdf` complaint_type: **missed** (got `None`)
- `sample3.pdf` initial_severity: **missed** (got `None`)
- `04_formal_letter.txt`: **error** BadRequestError: Error code: 400 - {'error': {'message': 'Tool choice is required, but model did not call a tool', 'type': 'invalid_request_error', 'code': 'tool_use_failed', 'failed_generation': '{\n  "complaint_source": "Sunrise Clinic",\n  "customer_name": "Dr. Anjali Nair",\n  "product_name": "A
- `04_formal_letter.txt` customer_name: **missed** (got `None`)
- `04_formal_letter.txt` product_name: **missed** (got `None`)
- `04_formal_letter.txt` product_strength: **missed** (got `None`)
- `04_formal_letter.txt` batch_number: **missed** (got `None`)
- `04_formal_letter.txt` manufacturing_date: **missed** (got `None`)
- `04_formal_letter.txt` expiry_date: **missed** (got `None`)
- `04_formal_letter.txt` quantity_affected: **missed** (got `None`)
- `04_formal_letter.txt` complaint_date: **missed** (got `None`)
- `04_formal_letter.txt` complaint_type: **missed** (got `None`)
- `04_formal_letter.txt` initial_severity: **missed** (got `None`)
- `05_informal_chat.txt` customer_name: **wrong** (got `Ravi`)
- `06_adverse_event.eml` customer_name: **wrong** (got `Dr. S. Iyer`)
- `06_adverse_event.eml` product_name: **wrong** (got `Ceftriaxone 1 g injection`)
- `06_adverse_event.eml` complaint_date: **wrong** (got `2026-09-03`)
- `07_ambiguous_dates.txt`: **error** BadRequestError: Error code: 400 - {'error': {'message': 'Tool choice is required, but model did not call a tool', 'type': 'invalid_request_error', 'code': 'tool_use_failed', 'failed_generation': '{\n  "complaint_source": "Phone",\n  "customer_name": "HealthKart Retail, New Delhi",\n  "product_name"
- `07_ambiguous_dates.txt` customer_name: **missed** (got `None`)
- `07_ambiguous_dates.txt` product_name: **missed** (got `None`)
- `07_ambiguous_dates.txt` product_strength: **missed** (got `None`)
- `07_ambiguous_dates.txt` batch_number: **missed** (got `None`)
- `07_ambiguous_dates.txt` manufacturing_date: **missed** (got `None`)
- `07_ambiguous_dates.txt` expiry_date: **missed** (got `None`)
- `07_ambiguous_dates.txt` quantity_affected: **missed** (got `None`)
- `07_ambiguous_dates.txt` complaint_date: **missed** (got `None`)
- `07_ambiguous_dates.txt` complaint_type: **missed** (got `None`)
- `07_ambiguous_dates.txt` initial_severity: **missed** (got `None`)
- `08_phone_transcript.txt`: **error** BadRequestError: Error code: 400 - {'error': {'message': 'Tool choice is required, but model did not call a tool', 'type': 'invalid_request_error', 'code': 'tool_use_failed', 'failed_generation': '{\n  "complaint_source": "Phone Call",\n  "customer_name": "Mr. Arjun Shah",\n  "product_name": "Insuli
- `08_phone_transcript.txt` customer_name: **missed** (got `None`)
- `08_phone_transcript.txt` product_name: **missed** (got `None`)
- `08_phone_transcript.txt` product_strength: **missed** (got `None`)
- `08_phone_transcript.txt` batch_number: **missed** (got `None`)
- `08_phone_transcript.txt` quantity_affected: **missed** (got `None`)
- `08_phone_transcript.txt` complaint_date: **missed** (got `None`)
- `08_phone_transcript.txt` complaint_type: **missed** (got `None`)
- `08_phone_transcript.txt` initial_severity: **missed** (got `None`)
- `10_two_batches.txt` initial_severity: **wrong** (got `Minor`)
