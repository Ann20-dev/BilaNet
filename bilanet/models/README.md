Model files for local development. The desktop app downloads its model itself (see app/inference/models.py).

Use one of these Q4_K_M GGUF files and point MODEL_PATH at it (or set MODELS_DIR to this folder and use the Download button):
- qwen2.5-coder-1.5b-instruct-q4_k_m.gguf  (Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF, ~1.1 GB) for 4-6 GB RAM laptops
- qwen2.5-coder-3b-instruct-q4_k_m.gguf    (Qwen/Qwen2.5-Coder-3B-Instruct-GGUF, ~2.1 GB) for 8 GB and up
The older qwen2.5-coder-3b-instruct-q4_0.gguf still works.
