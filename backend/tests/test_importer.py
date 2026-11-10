import io
from pathlib import Path

import pandas as pd
import pytest

from app.importer import ImportFileError, map_columns, read_table
from app.models import Complaint

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "complaints_bulk.xlsx"

GOOD_ROW = {"Customer": "Acme Pharmacy", "Product": "Paracetamol", "Batch No": "PCM-1",
            "Complaint Type": "Packaging", "Description": "Torn carton",
            "Severity": "Minor", "Complaint Date": "2026-09-01"}


def csv_bytes(rows: list) -> bytes:
    return pd.DataFrame(rows).to_csv(index=False).encode()


def upload(client, rows, dry_run=False, name="complaints.csv"):
    url = "/api/import" + ("?dry_run=true" if dry_run else "")
    return client.post(url, files={"file": (name, csv_bytes(rows))})


def test_header_variants_map_to_fields():
    mapping, ignored = map_columns(["Batch No.", "LOT", "batch_number", "Exp. Date",
                                    "Qty", "Colour"])
    assert mapping == {"Batch No.": "batch_number", "Exp. Date": "expiry_date",
                       "Qty": "quantity_affected"}
    assert ignored == ["LOT", "batch_number", "Colour"]   # second batch column ignored


def test_good_rows_are_saved_with_numbers(client, db_session):
    rows = [GOOD_ROW, {**GOOD_ROW, "Batch No": "PCM-2"}]
    report = upload(client, rows).json()
    assert report["imported"] == 2 and report["errors"] == []
    assert report["complaint_numbers"] == ["CMP-2026-0001", "CMP-2026-0002"]
    saved = db_session().query(Complaint).first()
    assert saved.complaint_source == "Bulk import"


def test_bad_rows_reported_good_rows_still_saved(client):
    rows = [GOOD_ROW,
            {**GOOD_ROW, "Batch No": "PCM-2", "Complaint Date": "next week"},
            {**GOOD_ROW, "Batch No": "PCM-3", "Severity": "Huge"},
            {**GOOD_ROW, "Batch No": ""}]
    report = upload(client, rows).json()
    assert report["imported"] == 1
    assert report["skipped"] == 3
    by_row = {e["row"]: e for e in report["errors"]}
    assert by_row[3]["field"] == "complaint_date"
    assert by_row[4]["field"] == "initial_severity"
    assert by_row[5] == {"row": 5, "field": "batch_number", "reason": "required"}


def test_dry_run_saves_nothing(client, db_session):
    report = upload(client, [GOOD_ROW], dry_run=True).json()
    assert report["dry_run"] is True
    assert report["valid"] == 1 and report["imported"] == 0
    assert db_session().query(Complaint).count() == 0


def test_duplicates_in_file_and_in_database(client):
    upload(client, [GOOD_ROW])
    report = upload(client, [GOOD_ROW, {**GOOD_ROW, "Batch No": "PCM-9"},
                             {**GOOD_ROW, "Batch No": "pcm-9 "}]).json()
    reasons = {e["row"]: e["reason"] for e in report["errors"]}
    assert "already in the database" in reasons[2]
    assert "earlier in this file" in reasons[4]   # same batch after trim + lowercase
    assert report["imported"] == 1


def test_missing_required_column_is_a_400(client):
    r = upload(client, [{"Customer": "A", "Product": "B"}])
    assert r.status_code == 400
    assert "batch_number" in r.json()["detail"]


def test_unsupported_file_type_is_a_400(client):
    r = client.post("/api/import", files={"file": ("notes.txt", b"hello")})
    assert r.status_code == 400


def test_excel_date_cells_are_understood(client):
    df = pd.DataFrame([{**GOOD_ROW, "Complaint Date": pd.Timestamp("2026-09-01")}])
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    r = client.post("/api/import", files={"file": ("c.xlsx", buf.getvalue())})
    assert r.json()["imported"] == 1


def test_sample_workbook_imports_35_and_reports_5(client):
    r = client.post("/api/import", files={"file": ("complaints_bulk.xlsx", SAMPLE.read_bytes())})
    report = r.json()
    assert report["imported"] == 35
    assert report["skipped"] == 5
    assert sorted({e["row"] for e in report["errors"]}) == [37, 38, 39, 40, 41]


def test_empty_file_is_rejected():
    with pytest.raises(ImportFileError):
        read_table("x.csv", b"Batch No,Customer\n")
