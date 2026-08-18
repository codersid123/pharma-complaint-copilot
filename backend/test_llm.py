from app.llm import fast_llm, reasoning_llm, FAST_MODEL, REASONING_MODEL

print("FAST:", FAST_MODEL)
print("REASONING:", REASONING_MODEL)
print("--- fast ---")
print(fast_llm.invoke("Reply with the single word: OK").content)
print("--- reasoning ---")
print(reasoning_llm.invoke(
    'Return only this JSON, nothing else: {"status": "working"}').content)