import email
import io
from email import policy


def text_from_pdf(data: bytes) -> str:
    import pdfplumber
    out = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            out.append(page.extract_text() or "")
    return "\n".join(out).strip()

def text_from_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs).strip()

def text_from_eml(data: bytes) -> str:
    msg = email.message_from_bytes(data, policy=policy.default)
    body = msg.get_body(preferencelist=("plain",))
    return (f"Subject: {msg.get('subject','')}\nFrom: {msg.get('from','')}\n\n"
            + (body.get_content() if body else ""))

def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return text_from_pdf(data)
    if name.endswith(".docx"):
        return text_from_docx(data)
    if name.endswith(".eml"):
        return text_from_eml(data)
    return data.decode("utf-8", errors="ignore")
