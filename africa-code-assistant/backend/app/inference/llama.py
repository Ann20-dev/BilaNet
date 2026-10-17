import os
class LlamaProvider:
    def __init__(self, path, context_size=4096, threads=4, max_tokens=1024):
        self.path = path; self.context_size = context_size; self.threads = threads; self.max_tokens = max_tokens; self.llm = None
    def _prompt(self, prompt):
        return "<|im_start|>user\n" + str(prompt) + "<|im_end|>\n<|im_start|>assistant\n"
    def load(self):
        if not self.path or not os.path.exists(self.path):
            raise FileNotFoundError("model not found")
        try:
            from llama_cpp import Llama
        except ImportError:
            raise RuntimeError("llama-cpp-python not installed")
        self.llm = Llama(model_path=self.path, n_ctx=self.context_size, n_threads=self.threads, verbose=False)
    def generate(self, prompt, max_tokens=None):
        if self.llm is None: self.load()
        out = self.llm(self._prompt(prompt), max_tokens=max_tokens or self.max_tokens, stop=['<|im_end|>'])
        return out["choices"][0]["text"]
    def stream(self, prompt, max_tokens=None):
        if self.llm is None: self.load()
        for chunk in self.llm(self._prompt(prompt), max_tokens=max_tokens or self.max_tokens, stream=True, stop=['<|im_end|>']):
            yield chunk["choices"][0]["text"]
