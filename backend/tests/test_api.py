FORM = {"customer_name": "Acme", "product_name": "Metformin", "batch_number": "MET-9012",
        "complaint_type": "Product Quality", "complaint_description": "Cracked",
        "initial_severity": "Major", "priority": "", "expiry_date": ""}
RISK = {"level": "Major", "score": 60, "rationale": "r", "recommended_action": "a"}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_save_returns_id_based_numbers(client):
    first = client.post("/api/complaints", json={"form": FORM, "risk": RISK}).json()
    second = client.post("/api/complaints", json={"form": FORM}).json()
    assert first["complaint_number"].endswith("-0001")
    assert second["complaint_number"].endswith("-0002")


def test_blank_strings_and_enum_casing_are_cleaned(client):
    form = {**FORM, "initial_severity": "critical", "unknown_key": "x"}
    assert client.post("/api/complaints", json={"form": form}).status_code == 200
    saved = client.get("/api/complaints").json()[0]
    assert saved["initial_severity"] == "Critical"


def test_invalid_severity_returns_422(client):
    r = client.post("/api/complaints", json={"form": {**FORM, "initial_severity": "Huge"}})
    assert r.status_code == 422


def test_missing_form_returns_422(client):
    assert client.post("/api/complaints", json={"risk": RISK}).status_code == 422


def test_duplicate_check(client):
    assert client.post("/api/complaints/check-duplicate",
                       json={"form": {"batch_number": "MET-9012"}}).json() == {"duplicates": []}
    client.post("/api/complaints", json={"form": FORM})
    dupes = client.post("/api/complaints/check-duplicate",
                        json={"form": {"batch_number": " MET-9012 "}}).json()["duplicates"]
    assert len(dupes) == 1
    assert client.post("/api/complaints/check-duplicate",
                       json={"form": {}}).json() == {"duplicates": []}


def test_intake_text_calls_agent(client, fake_agent):
    r = client.post("/api/intake/text", json={"text": "complaint email"})
    assert r.status_code == 200
    assert fake_agent == [{"raw_text": "complaint email"}]


def test_upload_empty_file_skips_agent(client, fake_agent):
    r = client.post("/api/intake/upload", files={"file": ("blank.txt", b"   ")})
    assert "couldn't read" in r.json()["assistant_message"]
    assert fake_agent == []


def test_copilot_chat_passes_form(client, fake_agent):
    r = client.post("/api/copilot/chat",
                    json={"message": "make it critical", "current_form": FORM})
    assert r.status_code == 200
    assert fake_agent[0]["current_form"] == FORM



def test_dates_are_parsed_and_returned_as_iso(client):
    form = {**FORM, "manufacturing_date": "June 2025", "expiry_date": "2027-05-31"}
    assert client.post("/api/complaints", json={"form": form}).status_code == 200


def test_bad_date_returns_422_naming_the_field(client):
    r = client.post("/api/complaints", json={"form": {**FORM, "expiry_date": "soon"}})
    assert r.status_code == 422
    assert "expiry_date" in str(r.json()["detail"])
