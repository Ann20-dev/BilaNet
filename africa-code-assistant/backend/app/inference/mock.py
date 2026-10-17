class MockProvider:
    def generate(self, prompt, max_tokens=256):
        return f"[mock] {prompt[:120]}"
    def stream(self, prompt, max_tokens=256):
        yield self.generate(prompt, max_tokens)
