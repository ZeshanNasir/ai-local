# ai-local

How much real engineering work can a developer Mac do with a local model, and at what cost in speed and memory?

`ai-local` answers that with measurements, not impressions. It runs open-weight models through [Ollama](https://ollama.com) on Apple Silicon, times them, scores them on small synthetic engineering tasks, and saves every result with the conditions it was measured under. It is not a model leaderboard, and it does not claim local models replace hosted ones.

## First run

Requirements: a Mac with Apple Silicon, Python 3.10 or newer (included with the Xcode Command Line Tools), and [Ollama](https://ollama.com/download) installed and running. Nothing else to install.

```sh
git clone https://github.com/ZeshanNasir/ai-local.git
cd ai-local
./lab
```

`./lab` then:

1. Checks the machine, Python and Ollama, and explains what is missing with a link to the official installer. It installs nothing.
2. Refuses to run if `OLLAMA_HOST` points anywhere other than this machine.
3. Lists the models that have published measurements and marks which are installed.
4. If the chosen model is missing, shows its size and asks before running `ollama pull`. Nothing is downloaded without a yes.
5. Runs a short benchmark: three warm throughput runs and the 15 synthetic tasks once. About a minute on the baseline machine once the model is loaded. The memory-stressing context ladder is not part of it.
6. Saves `report.md` and the raw JSON to `results/<timestamp>/`, with chip, memory, macOS, Ollama version and power source recorded.

`./lab --model gemma4:26b-mlx` skips the menu. The full CLI remains available: `python3 -m labbench --help`.

## Measured environment

All published results come from one machine: Apple M4 Pro, 48 GB unified memory, macOS 27.0.1, on AC power, Ollama 0.40.1 with flash attention and an 8-bit KV cache. Other chips and memory sizes have not been measured. `./lab` runs on them, says so, and the numbers it produces are your own first measurement, not a validated result.

## Selected findings (2026-10-09)

| Model | Decode tok/s | Prompt tok/s | Logs | Documents | Code fix, one shot | Largest completed context |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `qwen3.6:35b-mlx` | 68.3 | 991 | 16/18 | 24/24 | 3/3 | 67,901 tokens |
| `gemma4:26b-mlx` | 59.5 | 876 | 18/18 | 24/24 | 0/3 | 136,108 tokens |
| `qwen3.8:27b-mlx` | 26.1 | 137 | 15/18 | 24/24 | 3/3 | 67,152 tokens |

Throughput is the median of 5 warm runs (about 1,000-token prompt, 256-token cap, thinking off). Tasks ran 3 times each at temperature 0. The context column is the largest prompt recalled correctly before free memory fell to 13 to 15%, where the ladder stops.

- Decode speed differs by more than 2x between models of similar size.
- Long prompts hurt latency before memory: 2 to 12 minutes to the first token at about 67,000 tokens.
- One-shot and agent-loop results differ: `gemma4:26b-mlx` failed the code fix in one shot, but fixed it in each of three experimental agent sessions that could run the tests.
- The log and document tasks are too easy to separate the models. They show the method works, not which model is better at real work.

Full tables, including cold load, spread and every ladder step: `python3 -m labbench report benchmarks/results/2026-10-09`. Raw files: [`benchmarks/results/2026-10-09`](benchmarks/results/2026-10-09/).

## Method

- **Throughput:** one cold load, then warm runs with cache-busting prompts; timings are the server's own counters.
- **Workloads:** 6 log cases (does the evidence support the stated cause?), 8 document questions including stale and conflicting sources, and 1 bug fix checked by running its tests. Scoring is deterministic; no model grades another.
- **Context ladder:** a fact hidden mid-prompt at growing sizes, with memory and swap sampled throughout.

Definitions, protocol and settings: [`docs/methodology.md`](docs/methodology.md). The tasks and what they cannot show: [`docs/workloads.md`](docs/workloads.md). Break-even arithmetic with placeholder inputs (a calculator, not a result): [`docs/cost-model.md`](docs/cost-model.md).

## Limitations and privacy

- One machine, one day, one operator, small synthetic tasks, short generations, thinking off. A synthetic pass rate is not a production success rate.
- Not established: a fixed memory ceiling, the advertised 262,144-token context, cost savings, or whether each model is dense or mixture-of-experts.
- All tasks are synthetic. `./lab` talks only to Ollama on this machine and never calls a hosted model.
- A local model does not make the surrounding tools private. Editors, agent harnesses and tool servers can make their own connections: [`docs/privacy.md`](docs/privacy.md).
- **Experimental:** `python3 -m labbench agent` runs an [OpenCode](https://opencode.ai) session on the code-fix task. It is outside the standard workflow because OpenCode opened three to four connections to non-local endpoints in every session, even with a local-only config. Their purpose was not identified. The 9 saved sessions all fixed the bug; earlier debugging sessions that failed before a runner fix are not in the results. See [`docs/harness-compatibility.md`](docs/harness-compatibility.md).

## Contributing

Issues are welcome for errors in method, scoring or results. Include `report.md` from your run or the output of `python3 -m labbench env`. Tests need no model or network: `python3 -m unittest discover -s tests`.

## Licence

MIT. Written with AI assistance (Claude Code), then reviewed and run by the author. Every measurement is from a real run on the machine above.
