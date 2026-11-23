import gc
import os
import threading
import time


class LlamaProvider:
    """Runs the local GGUF model with llama.cpp.

    Built for low-memory laptops: the model is loaded on the first request, and unloaded
    again after `idle_unload` seconds without requests so its RAM goes back to the
    student's other apps (browser, editor). The next request reloads it (a few seconds).
    """

    def __init__(self, path, context_size=4096, threads=4, max_tokens=1024, idle_unload=300,
                 temperature=0.2, repeat_penalty=1.15):
        # `path` may be a function, so a model downloaded after startup is picked up without a restart.
        self._path = path
        self.context_size = context_size; self.threads = threads; self.max_tokens = max_tokens
        self.idle_unload = idle_unload
        self.sampling = {"temperature": temperature, "repeat_penalty": repeat_penalty}
        self.llm = None
        self.last_used = time.monotonic()
        # llama.cpp is not thread-safe and FastAPI runs requests in parallel threads.
        self.lock = threading.Lock()
        self._watcher = None

    @property
    def path(self):
        return self._path() if callable(self._path) else self._path

    def _prompt(self, prompt, system=None):
        head = "<|im_start|>system\n" + system + "<|im_end|>\n" if system else ""
        return head + "<|im_start|>user\n" + str(prompt) + "<|im_end|>\n<|im_start|>assistant\n"

    def load(self):
        path = self.path
        if not path or not os.path.exists(path):
            from fastapi import HTTPException
            raise HTTPException(503, "The AI model is not downloaded yet. Use the Download button to get it (one time).")
        try:
            from llama_cpp import Llama
        except ImportError:
            raise RuntimeError("llama-cpp-python not installed")
        # use_mmap (the default) lets the OS page the model file in and out instead of
        # copying it all into RAM, which helps a lot on 4 GB machines.
        self.llm = Llama(model_path=path, n_ctx=self.context_size, n_threads=self.threads,
                         use_mmap=True, use_mlock=False, verbose=os.getenv("LLAMA_VERBOSE") == "1")
        self._start_watcher()

    def unload(self):
        """Free the model's RAM. Safe to call at any time."""
        with self.lock:
            self._release()

    def _release(self):
        if self.llm is not None:
            llm, self.llm = self.llm, None
            close = getattr(llm, "close", None)
            if close:
                close()
            del llm
            gc.collect()

    def _start_watcher(self):
        if self.idle_unload <= 0 or (self._watcher and self._watcher.is_alive()):
            return
        self._watcher = threading.Thread(target=self._watch, daemon=True)
        self._watcher.start()

    def _watch(self):
        while True:
            time.sleep(min(30, self.idle_unload))
            # Skip if a request is running; it holds the lock.
            if not self.lock.acquire(blocking=False):
                continue
            try:
                if self.llm is None:
                    return
                if time.monotonic() - self.last_used >= self.idle_unload:
                    self._release()
                    return
            finally:
                self.lock.release()

    def generate(self, prompt, max_tokens=None, system=None):
        with self.lock:
            if self.llm is None: self.load()
            try:
                out = self.llm(self._prompt(prompt, system), max_tokens=max_tokens or self.max_tokens, stop=['<|im_end|>'], **self.sampling)
            except ValueError as e:
                # llama.cpp raises ValueError when the prompt does not fit in the context window.
                from fastapi import HTTPException
                raise HTTPException(413, "This is too long for the offline model. Send a smaller part of the code (about 150 lines or fewer).") from e
            finally:
                self.last_used = time.monotonic()
        return out["choices"][0]["text"]

    def stream(self, prompt, max_tokens=None, system=None):
        with self.lock:
            if self.llm is None: self.load()
            try:
                for chunk in self.llm(self._prompt(prompt, system), max_tokens=max_tokens or self.max_tokens, stream=True, stop=['<|im_end|>'], **self.sampling):
                    yield chunk["choices"][0]["text"]
            finally:
                self.last_used = time.monotonic()
