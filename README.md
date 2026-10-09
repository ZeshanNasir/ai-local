# ai-local

Which local AI model should you use on your Mac?

`./lab` tests the models you already have in [Ollama](https://ollama.com) for speed and accuracy on small engineering tasks, then prints one table.

```sh
git clone https://github.com/ZeshanNasir/ai-local.git
cd ai-local
./lab
```

```
Model              Speed  Accuracy  Verdict
gemma4:26b-mlx  60 tok/s     14/15  fast, missed code fix
```

That is a real run on an M4 Pro. Each model takes about a minute. The table and raw data are saved in `results/`. To test only some models: `./lab gemma4:26b-mlx`.

**You need** a Mac with Apple Silicon, Python 3.10 or newer, and Ollama with at least one model installed. Nothing else to install.

**It never** downloads a model, installs software or sends anything to another machine. If `OLLAMA_HOST` points elsewhere, it stops.

## Results

On an M4 Pro with 48 GB, the fastest of three models was more than twice as fast as the slowest, and none passed every task in every run. Full table, findings and method: [RESULTS.md](RESULTS.md).

## Tests

`python3 -m unittest discover -s tests` needs no model and no network.

MIT licence.
