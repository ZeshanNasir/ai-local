# ai-local

**Measures how fast, how accurately and at what memory cost local models handle everyday engineering tasks on an Apple Silicon Mac.**

Before routing work to a local model, you need numbers from your own machine: tokens per second, time to first token, how large a prompt fits before the system starts swapping, and whether answers to log, document and code tasks are actually correct. `ai-local` measures those with Ollama and small synthetic tasks, and records every result with the conditions it was measured under. It is not a leaderboard, and it does not claim local models replace hosted ones.

```sh
git clone https://github.com/ZeshanNasir/ai-local.git
cd ai-local
./lab
```

**Requirements:** Apple Silicon Mac, Python 3.10+ (part of the Xcode Command Line Tools), [Ollama](https://ollama.com/download) installed and running. No other dependencies.

**Consent before downloads:** `./lab` lists only models with published measurements. If the one you pick is missing, it shows the download size and runs `ollama pull` only after you answer yes.

## What `./lab` does

1. Checks the Mac, Python and Ollama; explains anything missing with a link to the official installer. Installs nothing.
2. Stops if `OLLAMA_HOST` points at another machine. Requests go only to Ollama on this Mac.
3. Runs a short benchmark: 3 warm throughput runs and 15 synthetic tasks once. About a minute on the baseline machine once the model is loaded. The memory-stressing context ladder is not included.
4. Saves `report.md` and raw JSON to `results/<timestamp>/`, with chip, memory, macOS, Ollama version and power source.

`./lab --model gemma4:26b-mlx` skips the menu. Every measurement is also available directly: `python3 -m labbench --help`.

## Measured environment

All published results come from one machine: Apple M4 Pro, 48 GB unified memory, macOS 27.0.1, on AC power, Ollama 0.40.1 with flash attention and an 8-bit KV cache. Other chips and memory sizes have not been measured. `./lab` runs on them, says so, and the numbers it produces are your own first measurement, not a validated result.

## Results (2026-10-09)

| Model | Decode tok/s | Prompt tok/s | Logs | Documents | Code fix, one shot | Largest completed context |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `qwen3.6:35b-mlx` | 68.3 | 991 | 16/18 | 24/24 | 3/3 | 67,901 tokens |
| `gemma4:26b-mlx` | 59.5 | 876 | 18/18 | 24/24 | 0/3 | 136,108 tokens |
| `qwen3.8:27b-mlx` | 26.1 | 137 | 15/18 | 24/24 | 3/3 | 67,152 tokens |

Throughput is the median of 5 warm runs (about 1,000-token prompt, 256-token cap, thinking off). Tasks ran 3 times each at temperature 0. The context column is the largest prompt recalled correctly before free memory fell to 13 to 15%, where the ladder stops.

What the numbers show:

- **Model design matters more than size.** Decode speed differs by more than 2x between models of similar parameter count, and `qwen3.8:27b-mlx` reads prompts about 7x slower than the other two.
- **Long prompts cost time before memory.** At about 67,000 tokens, the first token took 2 to 12 minutes. At that size, two of the three models had already pushed free memory down to 13 to 15% and into swap.
- **Test feedback changes the outcome.** `gemma4:26b-mlx` failed the code fix in all three one-shot attempts but fixed it in each of three experimental agent sessions that could run the tests.
- **The easy tasks do not rank models.** Every model passed all document cases. These tasks show the method works, not which model is better at real work.

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
