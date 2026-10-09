# ai-local

Measurements of practical local-AI engineering workloads on an Apple Silicon Mac, with every result file published.

The question is narrow: on one ordinary workstation, which engineering tasks run locally at acceptable quality, speed and memory use? This is not a model ranking, not a platform, and not a claim that local models replace hosted ones.

## Scope

- **Supported:** macOS on Apple Silicon, with [Ollama](https://ollama.com) as the runtime.
- **Measured baseline:** Apple M4 Pro, 48 GB unified memory, macOS 27.0.1, on AC power, Ollama 0.40.1 with flash attention and an 8-bit KV cache.
- **Not tested:** other chips, other memory sizes, other runtimes, Linux or Windows.

## Quick start

Requires Python 3.10 or newer. Standard library only; nothing to install.

```sh
git clone https://github.com/ZeshanNasir/ai-local.git && cd ai-local
python3 -m unittest discover -s tests      # 19 tests; no model, no network
python3 -m labbench env                    # machine and runtime snapshot
```

To measure, pull a model in Ollama yourself first. The runner never downloads models and never falls back to a hosted service.

```sh
python3 -m labbench throughput gemma4:26b-mlx --runs 5
python3 -m labbench workloads gemma4:26b-mlx --repeats 3
scripts/run_suite.sh gemma4:26b-mlx         # throughput, workloads and context ladder
python3 -m labbench report benchmarks/results/2026-10-09
```

Close heavy applications first. The context ladder deliberately pushes memory; read the stop conditions in [`docs/methodology.md`](docs/methodology.md) before running it.

## What is measured

| Measure | How |
| :--- | :--- |
| Throughput | Cold load, time to first token, prompt and decode tokens/s; median of 5 warm runs |
| Context ladder | A fact hidden mid-prompt at increasing sizes; stops when free memory or swap crosses a limit |
| Workloads | Synthetic log analysis, document questions (including stale and conflicting sources) and one code fix, scored deterministically |
| Retrieval | An embedding model against a BM25 baseline on a small question set |
| Cost | Break-even arithmetic from an assumptions file; a calculator, not a result |

Details: [`docs/methodology.md`](docs/methodology.md), [`docs/workloads.md`](docs/workloads.md), [`docs/cost-model.md`](docs/cost-model.md).

## Results (2026-10-09)

Measured on the baseline machine above. The desktop was in normal use, with about 12 GB of swap already in use before the runs, so memory figures are conservative. Raw files: [`benchmarks/results/2026-10-09`](benchmarks/results/2026-10-09/).

**Throughput** (about 1,000-token prompt, 256-token cap, thinking off, median of 5)

| Model | Time to first token | Prompt tok/s | Decode tok/s |
| :--- | ---: | ---: | ---: |
| `qwen3.6:35b-mlx` | 1.13 s | 991 | 68.3 |
| `gemma4:26b-mlx` | 1.25 s | 876 | 59.5 |
| `qwen3.8:27b-mlx` | 8.12 s | 137 | 26.1 |

**Workloads** (3 repeats per case, temperature 0)

| Model | Logs (6 cases) | Documents (8) | Code fix, one shot (1) |
| :--- | ---: | ---: | ---: |
| `qwen3.6:35b-mlx` | 16/18 | 24/24 | 3/3 |
| `gemma4:26b-mlx` | 18/18 | 24/24 | 0/3 |
| `qwen3.8:27b-mlx` | 15/18 | 24/24 | 3/3 |

**Largest completed context step** (fact recalled in every completed step)

| Model | Prompt tokens | Time to first token | Lowest free memory | Swap growth |
| :--- | ---: | ---: | ---: | ---: |
| `gemma4:26b-mlx` | 136,108 | 388 s | 13% | 1.8 GB |
| `qwen3.6:35b-mlx` | 67,901 | 150 s | 13% | 1.8 GB |
| `qwen3.8:27b-mlx` | 67,152 | 704 s | 15% | 3.2 GB |

Each of these steps crossed the runner's memory limit, so the ladder stopped there. Full ladder: `python3 -m labbench report`.

What this supports:

- Decode speed differs by more than 2x between the models tested. `qwen3.8:27b-mlx` also reads prompts 6 to 7 times slower.
- Long prompts become a latency problem before a memory problem: about 2.5 to 12 minutes to first token at about 67,000 tokens.
- The advertised 262,144-token context was not tested and is not claimed.
- The document and log tasks are too easy to separate the models. They show the method works, not which model is better at real work.
- The embedding model matched the BM25 baseline exactly on six queries. That is an integration check, not a quality result.

## Limitations

One machine, one day, one operator. Short generations, small synthetic tasks, thinking off, one runtime. Nothing here shows how these models perform on real operational data, on other hardware or in a team. A synthetic pass rate is not a production success rate.

Not established: a fixed memory ceiling for these models, the full advertised context, cost savings, and whether any model is dense or mixture-of-experts (local metadata does not say, except the `qwen3_5_moe` architecture tag on `qwen3.6:35b-mlx`). Earlier single-run figures in [`benchmarks/prior`](benchmarks/prior/README.md) were not repeated and are kept only for comparison.

## Privacy and execution boundaries

- All tasks and documents are synthetic. No private or employer data is used.
- The runner talks only to the Ollama server at `OLLAMA_HOST` (default `127.0.0.1:11434`). Pointing that variable at another machine makes inference remote. The runner does not download models or call hosted inference.
- Running a model locally does not, by itself, keep data on the machine. Any harness, editor or tool server around the model can make its own connections. See [`docs/privacy.md`](docs/privacy.md).

## Experimental: coding-agent harness

`python3 -m labbench agent` runs one bounded [OpenCode](https://opencode.ai) session on the code-fix task and scores it by running the tests. It is not part of the quick start because its network behaviour is unresolved: with a minimal local-only config, OpenCode still opened three to four connections to non-local endpoints in every session. Their purpose and content were not identified.

Saved results: 9 of 9 scored sessions (three per model) fixed the bug without editing tests, in 40 to 250 seconds. Before those runs, at least four debugging sessions failed or were stopped while the runner was being fixed. The main defect: OpenCode read `PWD` and worked in the wrong directory. Those sessions are not in the result files, and the nine scored runs do not show how often a first attempt succeeds in other setups. Details: [`docs/harness-compatibility.md`](docs/harness-compatibility.md).

## Contributing

Issues are welcome for errors in method or results. Please include the output of `python3 -m labbench env`.

## Licence

MIT. See [`LICENSE`](LICENSE).

The runner, tests and documents were written with AI assistance (Claude Code), then reviewed and run by the author. Measurements are from real runs on the machine above.
