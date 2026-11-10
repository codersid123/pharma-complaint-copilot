import io
from email.message import EmailMessage
from pathlib import Path

from docx import Document

from app.extract import extract_text

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def test_pdf_sample():
    text = extract_text("sample1.pdf", (SAMPLES / "sample1.pdf").read_bytes())
    assert "APX-2451" in text
    assert "Paracetamol" in text


def test_docx():
    doc = Document()
    doc.add_paragraph("Batch: DOC-77")
    buf = io.BytesIO()
    doc.save(buf)
    assert "DOC-77" in extract_text("letter.DOCX", buf.getvalue())


def test_eml_keeps_subject_date_and_body():
    msg = EmailMessage()
    msg["Subject"] = "Broken tablets"
    msg["From"] = "qa@pharmacy.example"
    msg["Date"] = "Fri, 04 Sep 2026 10:15:00 +0530"
    msg.set_content("Batch EML-5 had cracked tablets.")
    text = extract_text("mail.eml", msg.as_bytes())
    assert "Broken tablets" in text
    assert "EML-5" in text
    assert "04 Sep 2026" in text   # the sent date is often the complaint date


def test_txt_and_unknown_extension():
    assert extract_text("note.txt", b"Batch TXT-1") == "Batch TXT-1"
    assert extract_text("note", "Lot \xe9".encode()) == "Lot \xe9"
