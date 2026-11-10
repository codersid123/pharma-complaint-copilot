from app.agent import run_agent
from app.llm import LLMs


class R:
    def __init__(self, c): self.content = c


class Fake:
    def invoke(self, prompt):
        return R('{"customer_name": "Acme", "batch_number": "B-1", "colour": "red"}')


fake = LLMs(fast=Fake(), reasoning=Fake(), fast_model="fake", reasoning_model="fake")
print(run_agent(raw_text="any document", llms=fake))