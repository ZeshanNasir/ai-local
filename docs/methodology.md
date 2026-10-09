# Methodology

Every number in `benchmarks/results/` comes from `labbench` on the machine described in the file's `environment` block. Nothing is copied from a model card or a runtime's headline display.

## What is measured

| Measure | Definition |
| :--- | :--- |
| Cold start | Time the server reports to load the model after every model was unloaded (`load_duration`). |
| Time to first token | Request sent until the first streamed token, answer or reasoning. |
| Prompt throughput | `prompt_eval_count / prompt_eval_duration`, as reported by the server. |
| Decode throughput | `eval_count / eval_duration`. Output is capped at 256 tokens, so this is a short-generation figure, not a sustained one. |
| Memory | Three proxies, because unified memory has no single honest number: the server's reported resident size for the loaded model (`/api/ps`, includes the KV cache for the configured context), the lowest system-wide free-memory percentage seen while the request ran (`memory_pressure`, sampled every 3 s) and swap growth. |

## Protocol

1. All models are unloaded. Only one model is resident at a time.
2. **Throughput:** one cold run, then five warm runs of a roughly 1,000-token prompt. Each prompt starts with a different run id, so the server's prompt cache cannot reuse earlier work. The table reports the median of the warm runs and the spread, `(max - min) / median`; a large spread means the median should not be trusted.
3. **Workloads:** every case three times, temperature 0, fixed seed, thinking off (see below). A case passes only if every check passes.
4. **Context ladder:** a prompt of the target length with one fact hidden in the middle and a question about it at the end. A step passes only if the server reports a prompt of about the target length (so nothing was silently truncated) and the fact was recalled. The ladder stops at the first step that errors, drops free memory below 15% or grows swap by more than 2 GiB.
5. The environment snapshot is stored with every result: macOS, chip, memory, power source, runtime version, and the model under test with its digest and quantization (other installed models are counted, not listed).

## Settings that affect results

- Temperature 0, seed 1. Runs are repeatable in setup but not guaranteed bit-identical.
- Thinking is switched off (`think: false`) for all runs so that models are compared on answer latency and a fixed output cap. Quality with reasoning enabled is a different measurement and is not reported.
- The server runs with flash attention on and an 8-bit KV cache (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`). Both are in the environment of the measured server. Results with other settings may differ.
- `format: "json"` is not used: the MLX runner in the tested Ollama version answers it with HTTP 501. The prompts ask for JSON and the scorer extracts the first JSON object from the reply.

## Limits

- One machine, one operator, one day. Nothing here generalises to other hardware, other runtime versions or other workloads.
- Workloads are small and synthetic. A pass rate of 17/18 means 17 of 18 cases, not 94% of anything.
- Throughput is measured on short generations. Sustained decode over thousands of tokens, thermal throttling over an hour and concurrent use are not measured.
- Memory figures are proxies. Peak memory per process is not measured.
- Advertised context (metadata) is never reported as usable context. Only ladder steps that completed are reported as tested.
