# Executive Brief: Apple Silicon Local AI Standard

Empirical evaluation and hardware specification baseline for running local engineering AI models on Apple Silicon Macs, replacing routine cloud API token usage.

## The Core Question

> Can an in-stock, standard-procurement Apple Silicon Mac (48 GB unified memory) execute production-grade engineering tasks (incident log triage, multi-threaded concurrency code, architecture proofs) locally with zero cloud API costs and zero code leakage?

## Financial Case

* **Current Baseline**: 5 developers spending ~$5,000/mo ($60,000/yr) on cloud AI seats and token overages.
* **Standard Hardware Target**: MacBook Pro 16" Apple M5 Pro (48 GB unified RAM, 1 TB SSD, standard enterprise Atea SKU: `MGE64KS/A`, 37,843 SEK / ~$3,500 USD).
* **Payback Period**: ~3.5 months against recurring cloud token spend. Amortized hardware asset (CapEx) replacing uncapped cloud operating expense (OpEx).
* **Corporate Viability**: Avoids custom BTO 64 GB delay and eliminates budget rejection of $5,000+ luxury machines. 48 GB is standard in-stock enterprise procurement.

## Empirical Verification (Tested on Reference Host)

Measured on reference host (M4 Pro 48 GB, macOS 27, Ollama 0.40.2 MLX runner). All workloads executed inside unified memory with zero SSD swap:

| Fleet Role | Model Tag | Throughput | Real Engineering Task Tested | Pass / Proof |
| :--- | :--- | :--- | :--- | :--- |
| **Heavy Engineering** | `qwen3.6:35b-mlx` | 70.6 tok/s | Multi-region Raft consensus partition proof (9,915 tokens) | Verified Leader Completeness & Lease Bounds |
| **Fast Interactive Triage** | `gemma4:26b-mlx` | 59.4 tok/s (0.7s TTFT) | Log analysis & fast triage in 1m 16s | Sub-second ingestion |
| **Deep Concurrency Logic** | `qwen3.8:27b-mlx` | 28.8 tok/s | Multi-threaded FIFO rate limiter with no thread starvation | Passed live concurrency test suite (15 threads) |

## Hardware Alignment: M5 Pro (48 GB) vs. Current Host

* **Memory Bandwidth**: ~273 GB/s (M4 Pro) $\rightarrow$ ~350–380 GB/s (M5 Pro).
* **Target Throughput on 27B**: Sustained 45–50 tok/s, bursting past 60 tok/s with native MLX Multi-Token Prediction (MTP draft acceptance rate measured at 87%).
* **Memory Headroom**: A 27B–35B model (18–23 GB) leaves ~25 GB unified memory for Docker, IDEs, and local developer toolchains without memory pressure.

## Boundary Invariant

Local models handle high-volume routine engineering workloads (unit testing, boilerplate, log parsing, git commits). Cloud models remain available for rare cross-repository architectural escalations.
