from app.models import Complaint
from app.seed import build_rows, seed


def test_rows_are_the_same_every_time():
    a = [(c.batch_number, c.complaint_date) for c in build_rows()]
    b = [(c.batch_number, c.complaint_date) for c in build_rows()]
    assert a == b


def test_seed_only_fills_an_empty_table(db_session):
    db = db_session()
    assert seed(db) == 50
    assert seed(db) == 0                     # second run does nothing
    assert db.query(Complaint).count() == 50
    assert seed(db, reset=True) == 50        # --reset replaces, doesn't add
    assert db.query(Complaint).count() == 50


def test_every_row_has_a_number_and_valid_dates(db_session):
    db = db_session()
    seed(db)
    for c in db.query(Complaint):
        assert c.complaint_number.startswith("CMP-")
        assert c.expiry_date > c.manufacturing_date
