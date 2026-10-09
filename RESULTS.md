# Results

Measured on 2026-10-09 on an Apple M4 Pro with 48 GB, macOS 27.0.1, Ollama 0.40.1, on AC power. Each model ran every task three times. Raw files: [`benchmarks/results/2026-10-09`](benchmarks/results/2026-10-09/).

| Model | Speed | Tasks passed | Verdict |
| :--- | ---: | ---: | :--- |
| `qwen3.6:35b-mlx` | 68 tok/s | 43/45 | fast, missed a log task in 2 of 3 runs |
| `gemma4:26b-mlx` | 60 tok/s | 42/45 | fast, missed the code fix in every run |
| `qwen3.8:27b-mlx` | 26 tok/s | 42/45 | slow, missed a log task in every run |

## What else was found

- **Long prompts cost minutes.** At about 67,000 tokens, the first word took 2 to 12 minutes, and two of the three models pushed the Mac into swap. The advertised 262,144-token context was not tested.
- **Letting a model run the tests helps.** `gemma4:26b-mlx` failed the code fix when answering in one go, but fixed it in three of three sessions in the OpenCode coding agent, where it could run the tests.
- **Local is not automatically private.** Ollama only used this machine. OpenCode, the agent around it, also connected to outside servers whose purpose was not identified.

The long-prompt and agent tests are not part of `./lab` any more. Their raw files are kept with the others.

## How it is measured

- **Speed:** median decode speed over 3 warm runs of a 1,000-token prompt, from Ollama's own timings. Thinking is off.
- **Tasks passed:** 15 synthetic tasks, checked by code, not by another model. 6 ask whether a log supports a stated cause, 8 ask questions about short documents (some stale or conflicting), 1 asks for a bug fix that must pass its tests. This counts passes on small tasks; it is not general model accuracy.
- **Fast** means 40 tokens per second or more. That is a local rule of thumb, not a standard.

One machine, one day, small synthetic tasks. This does not predict how a model performs on your real work.
