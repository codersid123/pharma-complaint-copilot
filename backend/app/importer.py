"""Bulk import: turn a CSV or Excel sheet into complaint records.

Every row is checked with the same rules as a manual save (SavedForm), so an
import can never put data in the database that the form couldn't.
"""
import io
import re
from datetime import date

import pandas as pd
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .agent import REQUIRED
from .models import Complaint
from .schemas import SavedForm


class ImportFileError(ValueError):
    """The file itself can't be read (wrong type, empty, no usable columns)."""


def _key(header: str) -> str:
    """'Batch No.' -> 'batchno', 'batch_number' -> 'batchnumber'."""
    return re.sub(r"[^a-z0-9]", "", str(header).lower())


# Every header spelling we accept, mapped to a form field. Keys are already
# normalised with _key(), so case, spaces and punctuation don't matter.
HEADER_MAP = {
    **{k: "complaint_source" for k in ["complaintsource", "source", "channel"]},
    **{k: "customer_name" for k in ["customername", "customer", "complainant", "reportedby"]},
    **{k: "product_name" for k in ["productname", "product", "drug", "item"]},
    **{k: "product_strength" for k in ["productstrength", "strength", "dose", "grade"]},
    **{k: "batch_number" for k in ["batchnumber", "batchno", "batch", "lot", "lotno",
                                   "lotnumber", "batchlot", "batchlotnumber"]},
    **{k: "manufacturing_date" for k in ["manufacturingdate", "mfgdate", "mfg", "mfddate",
                                         "dateofmanufacture"]},
    **{k: "expiry_date" for k in ["expirydate", "expdate", "exp", "expiry", "expiration",
                                  "expirationdate"]},
    **{k: "quantity_affected" for k in ["quantityaffected", "quantity", "qty", "qtyaffected"]},
    **{k: "complaint_type" for k in ["complainttype", "type", "category"]},
    **{k: "complaint_date" for k in ["complaintdate", "date", "datereceived", "receivedon",
                                     "reportdate"]},
    **{k: "complaint_description" for k in ["complaintdescription", "description", "details",
                                            "complaint", "issue", "remarks"]},
    **{k: "initial_severity" for k in ["initialseverity", "severity"]},
    **{k: "priority" for k in ["priority"]},
}


def read_table(filename: str, data: bytes) -> pd.DataFrame:
    """Read every cell as text, so '0042' stays '0042' and blanks stay ''."""
    name = filename.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(data), dtype=str, keep_default_na=False)
        else:
            raise ImportFileError("Only .csv and .xlsx files are supported.")
    except ImportFileError:
        raise
    except Exception as e:  # pandas raises many types for unreadable files
        raise ImportFileError(f"Could not read the file: {e}") from e
    if df.empty:
        raise ImportFileError("The file has no data rows.")
    return df


def map_columns(columns) -> tuple[dict, list]:
    """Return ({original header: field}, [headers we ignored])."""
    mapping, ignored = {}, []
    for col in columns:
        field = HEADER_MAP.get(_key(col))
        if field and field not in mapping.values():
            mapping[col] = field
        else:
            ignored.append(str(col))
    return mapping, ignored


def _row_errors(row_no: int, exc: ValidationError) -> list:
    out = []
    for err in exc.errors():
        field = str(err["loc"][0]) if err["loc"] else "row"
        reason = err["msg"].removeprefix("Value error, ")
        out.append({"row": row_no, "field": field, "reason": reason})
    return out


def same_complaint_key(batch, customer, complaint_date) -> tuple:
    """Same batch + customer + complaint date = the same complaint logged twice."""
    return ((batch or "").strip().lower(), (customer or "").strip().lower(), complaint_date)


def import_rows(df: pd.DataFrame, db: Session, dry_run: bool = False) -> dict:
    mapping, ignored = map_columns(df.columns)
    missing_cols = [f for f in REQUIRED if f not in mapping.values()]
    if missing_cols:
        raise ImportFileError(
            "Missing required column(s): " + ", ".join(missing_cols)
            + ". Found: " + ", ".join(map(str, df.columns)))

    existing = {same_complaint_key(*row) for row in
                db.query(Complaint.batch_number, Complaint.customer_name, Complaint.complaint_date)}

    errors, good, seen = [], [], set()
    for i, raw in enumerate(df.to_dict(orient="records")):
        row_no = i + 2  # row 1 is the header, so data starts at spreadsheet row 2
        values = {field: raw[col] for col, field in mapping.items()}
        if not any(str(v).strip() for v in values.values()):
            continue  # fully blank row: skip silently

        try:
            form = SavedForm(**values)
        except ValidationError as e:
            errors.extend(_row_errors(row_no, e))
            continue

        missing = [f for f in REQUIRED if getattr(form, f) in (None, "")]
        if missing:
            errors.extend({"row": row_no, "field": f, "reason": "required"} for f in missing)
            continue

        key = same_complaint_key(form.batch_number, form.customer_name, form.complaint_date)
        if key in existing or key in seen:
            where = "already in the database" if key in existing else "earlier in this file"
            errors.append({"row": row_no, "field": "batch_number",
                           "reason": f"duplicate: same batch, customer and date {where}"})
            continue
        seen.add(key)
        good.append(form)

    numbers = []
    if not dry_run and good:
        from .main import complaint_number  # local import avoids a circular import
        rows = []
        for form in good:
            data = form.model_dump()
            data["complaint_source"] = data["complaint_source"] or "Bulk import"
            c = Complaint(**data)
            db.add(c)
            rows.append(c)
        db.flush()  # all inserts get ids; nothing is committed yet
        for c in rows:
            c.complaint_number = complaint_number(c.id, (c.complaint_date or date.today()).year)
            numbers.append(c.complaint_number)
        db.commit()  # one transaction: all good rows, or none if anything fails

    error_rows = {e["row"] for e in errors}
    return {
        "dry_run": dry_run,
        "total_rows": len(good) + len(error_rows),
        "imported": 0 if dry_run else len(good),
        "valid": len(good),
        "skipped": len(error_rows),
        "errors": errors,
        "ignored_columns": ignored,
        "complaint_numbers": numbers,
    }
