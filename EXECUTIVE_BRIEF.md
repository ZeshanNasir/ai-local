# Executive Brief: Apple Silicon Local AI Standard

Empirical baseline and hardware specification for evaluating local engineering AI models on Apple Silicon Macs, replacing metered cloud API token usage.

## The Core Question

> Can an in-stock, standard-procurement Apple Silicon Mac (48 GB unified memory) execute production-grade engineering tasks (incident log triage, multi-threaded concurrency code, architecture proofs) locally with zero cloud API costs and zero code leakage?

## Financial Case: Metered OpEx vs. 4-Year Amortized CapEx

* **Enterprise Cloud Model (Variable OpEx)**: Billed per million tokens ($3.00–$15.00 input / $15.00–$75.00 output) plus enterprise platform seat commitments. Active agentic development (50M–150M tokens/developer/month) scales cloud expenditure exponentially with team size and context expansion.
* **Standard Hardware Target (Fixed CapEx)**: MacBook Pro 16" Apple M5 Pro (48 GB unified RAM, 1 TB SSD, standard enterprise Atea SKU: `MGE64KS/A`, 37,843 SEK / ~$3,500 USD).
* **Lifecycle Economics**: Amortized over standard 3.5 to 4-year (42–48 month) corporate PC refresh cycles, hardware cost is **~$73–$83/month per developer** with **$0.00 incremental cost per token**.
* **Procurement Advantage**: In-stock enterprise SKU eliminates custom BTO 64 GB shipping delays and avoids budget rejection of non-standard high-spec requests.

## Active Runtime Configuration (Verified on Reference Host)

Managed natively by macOS `launchd` via standard Homebrew service (`~/Library/LaunchAgents/sh.brew.ollama.plist`):

* `OLLAMA_FLASH_ATTENTION=1`: Fused Metal attention kernel.
* `OLLAMA_KV_CACHE_TYPE=q8_0`: Quantized 8-bit KV buffer saving ~50% VRAM (64K–100K context fits in unified RAM without swap).
* `Speculative Decoding`: Native MLX Multi-Token Prediction (MTP draft acceptance rate measured at 87%, 1.53x throughput multiplier).
* `Memory Policy`: Single model active in unified RAM; unloads cleanly to 0 MB VRAM when idle.

## Four-Tier Native Model Fleet

| Architecture Tier | Model Tag | Format / Quant | Purpose & Verified Performance |
| :--- | :--- | :--- | :--- |
| **System 1 Decision Engine** | `clef-flash:9b` | GGUF / Q8_0 | Sub-100ms policy, classification & routing via native `/v1/systemone` |
| **Semantic Embedding** | `embeddinggemma-2:740m-mxfp8` | SafeTensors / MXFP8 | 768-dimensional vector embeddings via native `/api/embed` for local code search |
| **Daily Interactive Workhorse** | `gemma4:26b-mlx` | SafeTensors / NVFP4 | 0.73s TTFT, 59.4 tok/s for routine daily dev, triage, and screenshots |
| **Deep Concurrency Reasoner** | `qwen3.8:27b-mlx` | SafeTensors | Deep multi-turn reasoning; 100% pass on 15-thread FIFO rate limiter |

## Stakeholder Verification Matrix

* **CISO / Information Security**: Zero data leaves the machine. Ollama binds strictly to loopback (`127.0.0.1`). Full SOC 2 and ISO 27001 data residency compliance.
* **Software Engineering Lead**: Standard developer workflow. Agents connect directly to native endpoints via `ollama launch <agent> --model <model>`.
* **IT Operations**: Standard Homebrew package management. Standard in-stock enterprise Atea SKU. Native macOS `launchd` service management.
* **Finance**: Replaces variable, uncapped monthly token invoices with fixed, amortized 4-year PC hardware CapEx.
