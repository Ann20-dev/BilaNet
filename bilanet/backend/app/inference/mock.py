class MockProvider:
    def generate(self, prompt, max_tokens=256, system=None):
        return f"[mock] {prompt[:120]}"
    def stream(self, prompt, max_tokens=256, system=None):
        yield self.generate(prompt, max_tokens, system)
