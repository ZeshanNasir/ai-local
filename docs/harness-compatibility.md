# Harness compatibility

What was actually run, on 2026-10-09, on the machine described in the README.

| Harness | Version | Model backend | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| OpenCode | 1.18.35 | Ollama through its OpenAI-compatible endpoint (`/v1`), local | **Tested, experimental.** Three scored sessions each with `qwen3.6:35b-mlx`, `gemma4:26b-mlx` and `qwen3.8:27b-mlx`; all nine fixed the task. Earlier debugging sessions that failed before the runner fix below are not recorded. Network behaviour unresolved; see [`privacy.md`](privacy.md) | `benchmarks/results/*/*.agent.json` |
| Claude Code | installed | Ollama (documented in the operator's notes) | **Not tested in this pass.** Whether it runs against a local model, and with what tool support, is unverified | none |
| Goose | not installed | none | **Not installed.** Unverified | none |
| DeepSeek-related harness (`dsh`) | not installed | none | **Not installed.** A wrapper script exists in the operator's private repository; the binary it launches was not present | none |
| MLX-LM directly | `mlx` 0.32.3 installed, `mlx_lm` not installed | none | **Not tested.** All MLX results here go through Ollama's MLX runner | none |

## What the OpenCode test did

For each model, three times: copy the synthetic coding project into a fresh temporary directory, run `opencode run` with a throwaway config that contains only the local Ollama provider, and give it the task of fixing the failing tests without editing them. Pass means the tests pass afterwards and no test file changed. Sessions took 40 to 250 seconds with 6 to 9 tool calls.

Two things to know when reading it:

- OpenCode reads the `PWD` environment variable rather than the process working directory. A runner that only sets the working directory makes the agent edit and test the wrong project. The runner sets `PWD`; this was found when the first attempts reported tests from an unrelated project.
- Through the OpenAI-compatible endpoint the model was loaded with its default context. `qwen3.8:27b-mlx` showed a 131,072-token context and 31 GB resident for a short session. Configured context, not the size of the task, drives memory use.

## Model-specific notes

- The MLX runner in the tested Ollama version rejects `format: "json"` with HTTP 501. Prompts ask for JSON and the scorer extracts it.
- Every model passes the agent task but not every model passes it in one shot: `gemma4:26b-mlx` failed the one-shot version three times and passed all three agent sessions. A test-feedback loop changes the answer.

## Not claimed

That every model works with every harness, that tool calling is equally reliable across models, or anything about harnesses not listed as tested.
