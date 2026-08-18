from app.extract import extract_text

path = "../samples/sample1.pdf"
with open(path, "rb") as f:
    text = extract_text(path, f.read())
print(f"Extracted {len(text)} characters:\n")
print(text[:800])