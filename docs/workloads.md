# Workloads

All inputs are synthetic and live in `data/synthetic/`. They contain no real logs, documents or code from any employer.

## Logs (`logs.json`, 6 cases)

Short numbered log excerpts in the style of Azure, AWS and Google Cloud, with a question. Three cases contain evidence of a cause (an expired client secret, a bucket-policy change, a CPU quota error). Three do not: the logs show symptoms only, and the correct answer is to say the cause is not supported.

Passing requires valid JSON, the correct decision on whether the logs support a conclusion, and (when they do) citing the required lines with at most two extra.

## Documents (`docs/`, `questions.json`, 8 cases)

Six short documents and eight questions: four answerable, two answerable only by preferring the newer of two policy documents, one with two undated documents that disagree (the answer is "conflict") and two the documents do not cover (the answer is "insufficient").

Passing requires the right status, the right source documents and, for answers, the key fact.

## Code (`coding/repo`, 1 case)

A tiny Python project with two failing unit tests (rounding and input validation). The model must return one complete file. The patch is applied to a temporary copy and the tests are run. It fails if tests still fail, if a test file is edited, or if the model writes outside an existing file.

This measures one-shot patching, not an agent loop. Agent behaviour is in `harness-compatibility.md`.

## Retrieval (embedding model)

The eight questions are run against the six documents with an embedding model and with a plain BM25 baseline. Reported: recall@1 and mean reciprocal rank over the questions that have relevant documents. Embedding quality is reported separately from answer quality because they are different jobs.

## What these workloads cannot show

They are small, written by one person, and easier than real operational data. They can show that a configuration does or does not handle the *shape* of a task (abstaining, citing, refusing to guess). They cannot show production reliability.
