# local-ai-engineering-lab

Can an ordinary engineering workstation run useful AI-assisted engineering tasks locally, at acceptable quality, speed and memory use, without sending every request to a hosted model?

This project measures that on one machine, with a small runner, synthetic tasks and every result file published. It reports what was measured, what was only claimed elsewhere, and where local inference stops being sensible. It does not say local models replace hosted ones.

Machine tested: Apple M4 Pro, 48 GB unified memory, macOS 27.0.1, on AC power, Ollama 0.40.1 with flash attention on and an 8-bit KV cache. The desktop was in normal use during the runs (the environment record shows about 12 GB of swap already in use before the benchmarks started), so memory results are conservative for a clean machine.

## What was found (2026-10-09)

- **Speed differs by an order of magnitude with model design.** The two mixture-of-experts models decoded at about 60 to 70 tokens/s and read prompts at about 900 to 1,000 tokens/s. The dense 27B model decoded at 26 tokens/s and read prompts at about 137 tokens/s.
- **Long prompts are a latency problem before they are a memory problem.** All three models recalled a fact hidden in a prompt of about 67,000 tokens. The dense model needed 11.7 minutes before its first token at that size; the mixture-of-experts models needed about 2.5 minutes. One model also completed a 136,000-token prompt (6.5 minutes).
- **The advertised 262,144-token context was not tested and is not claimed.** The largest completed prompt was 136,108 tokens. At that size, and at about 68,000 tokens for the other two, free memory fell to 13 to 15% and swap grew by 1.8 to 3.2 GB, which is where the runner stops.
- **One-shot patching and agent loops give different answers.** Asked for a fix in a single reply, one model failed a subtle rounding task three times out of three. Inside an agent loop that can run the tests, all three models fixed it in every one of three runs.
- **The document and log tasks are too easy to separate the models.** Every model passed all 24 document cases. Log analysis passed 15 to 18 of 18. These tasks show the method works, not which model is better at real work.
- **Local inference does not make the harness private by itself.** In a minimal OpenCode configuration the model server only used loopback, but the harness opened connections to two non-local endpoints. Their purpose was not identified. See [`docs/privacy.md`](docs/privacy.md).

#### Throughput (warm, about 1,000-token prompt, 256-token cap, median of 5 runs)

| Model | Cold load | Time to first token | Prompt tok/s | Decode tok/s | Decode spread |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `gemma4:26b-mlx` | 5.4 s | 1.25 s | 876 | 59.5 | 2% |
| `qwen3.6:35b-mlx` | 6.9 s | 1.13 s | 991 | 68.3 | 7% |
| `qwen3.8:27b-mlx` | 2.9 s | 8.12 s | 137 | 26.1 | 11% |

#### Workloads (3 repeats per case, temperature 0)

| Model | Logs (6 cases) | Documents (8) | Code (1) | Median wall time per case |
| :--- | ---: | ---: | ---: | ---: |
| `gemma4:26b-mlx` | 18/18 | 24/24 | 0/3 | 0.7 s |
| `qwen3.6:35b-mlx` | 16/18 | 24/24 | 3/3 | 0.6 s |
| `qwen3.8:27b-mlx` | 15/18 | 24/24 | 3/3 | 1.6 s |

#### Context ladder (fact hidden mid-prompt; stops at the first unsafe step)

| Model | Prompt tokens | Recalled | Prompt tok/s | Time to first token | Server-reported memory | Lowest free memory | Swap growth |
| :--- | ---: | :---: | ---: | ---: | ---: | ---: | ---: |
| `gemma4:26b-mlx` | 8,278 | yes | 731 | 11 s | 19.5 GB | 43% | 0 MB |
| `gemma4:26b-mlx` | 33,489 | yes | 615 | 55 s | 21.5 GB | 41% | 0 MB |
| `gemma4:26b-mlx` | 67,686 | yes | 494 | 137 s | 25.0 GB | 30% | 0 MB |
| `gemma4:26b-mlx` | 136,108 | yes | 351 | 388 s | 25.3 GB | 13% | 1804 MB | **stopped: unsafe**
| `qwen3.6:35b-mlx` | 8,289 | yes | 854 | 10 s | 24.2 GB | 32% | 0 MB |
| `qwen3.6:35b-mlx` | 33,576 | yes | 640 | 53 s | 25.5 GB | 26% | 0 MB |
| `qwen3.6:35b-mlx` | 67,901 | yes | 455 | 150 s | 27.8 GB | 13% | 1834 MB | **stopped: unsafe**
| `qwen3.8:27b-mlx` | 8,200 | yes | 123 | 67 s | 19.8 GB | 47% | 0 MB |
| `qwen3.8:27b-mlx` | 33,199 | yes | 110 | 301 s | 23.4 GB | 36% | 0 MB |
| `qwen3.8:27b-mlx` | 67,152 | yes | 95 | 704 s | 29.9 GB | 15% | 3197 MB | **stopped: unsafe**


Per-case failures: `gemma4:26b-mlx` failed the one-shot code case (3/3 runs); `qwen3.6:35b-mlx` failed one log case (it claimed a cause the logs do not support) in two of three runs; `qwen3.8:27b-mlx` failed one log case (cited too many extra lines) in all three runs. Agent sessions (OpenCode, three per model, scored by running the tests): all nine fixed the bug without editing tests, in 40 to 250 seconds. Raw files: [`benchmarks/results/`](benchmarks/results/2026-10-09/).

Embedding model `embeddinggemma-2:740m-mxfp8` (744M parameters, 1.3 GB resident, 768-dimension output) matched the BM25 baseline exactly: recall@1 1.0 and MRR 1.0 for both on six queries. The set is too small to separate them; this is a working integration check, not a quality ranking.

## Claims checked

| Claim | Status |
| :--- | :--- |
| About 70 tokens/s on these models | **Qualified.** Median 68 tokens/s for `qwen3.6:35b-mlx`, 60 for `gemma4:26b-mlx`, 26 for `qwen3.8:27b-mlx`, over 256-token generations with thinking off. Earlier single-run logs ([`benchmarks/prior`](benchmarks/prior/README.md)) showed up to 79; they used a different prompt and were not repeated. |
| A 48 GB machine keeps these models within about 38 GB | **Not established.** The server reports 25 to 30 GB resident up to about 68,000 tokens, but that figure is a proxy and system memory pressure appeared at the sizes above. No 38 GB limit was measured. |
| 256K context | **Not tested.** The metadata says 262,144. The largest completed prompt was 136,108 tokens, one model only. |
| Models run locally through coding-agent harnesses | **Verified for OpenCode** (nine scored sessions). Not tested for Claude Code, Goose or the DeepSeek harness; see [`docs/harness-compatibility.md`](docs/harness-compatibility.md). |
| Local inference keeps task data on the machine | **Not established.** Model traffic stayed on loopback; the harness still contacted outside endpoints. |
| Local inference saves money | **Not measured.** There is a calculator, not a result: [`docs/cost-model.md`](docs/cost-model.md). |

## Models

Identified from `ollama show` on the machine; licence text is the one bundled with each package.

| Tag | Parameters (total) | Architecture tag | Quantization | Licence |
| :--- | ---: | :--- | :--- | :--- |
| `qwen3.8:27b-mlx` | 27.8B | `qwen3_5` | nvfp4 | Apache-2.0 |
| `qwen3.6:35b-mlx` | 36.0B | `qwen3_5_moe` | nvfp4 | Apache-2.0 |
| `gemma4:26b-mlx` | 26.2B | `gemma4` | nvfp4 | Apache-2.0 |
| `embeddinggemma-2:740m-mxfp8` | 744M | `embedding_gemma2` | mxfp8 | not included in the package; check the model card |

Active-parameter counts (the "A3B" and "A4B" in published model names) and whether a model is dense or mixture-of-experts are not shown by the local metadata and were not independently verified. Hosted models (for example Cloudflare Workers AI) are remote inference and are not part of this project's local results.

## Reproduce

Python 3.10 or newer; standard library only. A local Ollama with the models pulled is needed to measure; the tests need nothing.

```sh
python3 -m unittest discover -s tests          # 19 tests, no model, no network
python3 -m labbench env                        # machine and runtime snapshot
python3 -m labbench throughput gemma4:26b-mlx --runs 5
python3 -m labbench workloads gemma4:26b-mlx --repeats 3
python3 -m labbench ladder gemma4:26b-mlx --sizes 8192,32768,65536
python3 -m labbench retrieval embeddinggemma-2:740m-mxfp8
LABBENCH_WORKDIR=/some/dir python3 -m labbench agent gemma4:26b-mlx --repeats 3   # needs OpenCode
python3 -m labbench report benchmarks/results/2026-10-09   # regenerate the tables above
```

`scripts/run_suite.sh` runs the first three for a list of models, one at a time. Close heavy applications first and read the stop conditions in [`docs/methodology.md`](docs/methodology.md) before running the ladder: it deliberately pushes memory.

## Documents

- [`docs/methodology.md`](docs/methodology.md): measures, protocol, settings, limits.
- [`docs/workloads.md`](docs/workloads.md): the synthetic tasks and what they cannot show.
- [`docs/harness-compatibility.md`](docs/harness-compatibility.md): what was tested, what was not.
- [`docs/privacy.md`](docs/privacy.md): what was observed about network use, and what was not.
- [`docs/cost-model.md`](docs/cost-model.md): per-task and per-seat arithmetic with placeholder inputs.

## Limits

One machine, one day, one operator. Short generations, small synthetic workloads, thinking off, one runtime. Nothing here establishes how any of these models performs on real operational data, on other hardware or in a team. A synthetic pass rate is not a production success rate.

## Provenance

The runner, tests and documents were written with AI assistance (Claude Code) and reviewed and run by the author; commits carry the co-author trailer. The measurements are from real runs on the machine above. The earlier private shell script this grew out of (`ai-bench`) is not included; its old results are in `benchmarks/prior` with the caveats stated there.

## Licence

MIT. See `LICENSE`.
