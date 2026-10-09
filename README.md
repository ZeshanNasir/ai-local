# ai-local

Test a local AI model on your Apple Silicon Mac. It shows how fast the model is and how many of 15 small engineering tasks it passes, so you can judge which routine work might run locally instead of on a paid cloud model.

For engineers who use a Mac with [Ollama](https://ollama.com).

```sh
git clone https://github.com/ZeshanNasir/ai-local.git
cd ai-local
./lab
```

You need a Mac with Apple Silicon, Python 3.10 or newer, and Ollama installed and running. Nothing else.

`./lab` lists the three models measured in [RESULTS.md](RESULTS.md) and asks you to pick one. A test takes about a minute. It prints one table and saves it in `results/`:

```
Model              Speed  Tasks passed  Verdict
gemma4:26b-mlx  60 tok/s         14/15  fast, missed code fix
```

That is a real run on an M4 Pro. To skip the picker: `./lab gemma4:26b-mlx`.

## Before anything is downloaded

If the model you pick is not installed, `./lab` asks `Download it with ollama pull MODEL? [y/N]`. Models are large. Only `y` downloads it. Any other answer downloads nothing and tests nothing.

It never installs Ollama or any other software. It never sends anything to another machine. If `OLLAMA_HOST` points elsewhere, it stops.

## What the results can and cannot tell you

They show speed on your Mac, and how a model does on 15 small synthetic tasks. They do not show that a local model can replace a cloud model, rank models in general, or promise any saving. Measured on one M4 Pro with 48 GB, on one day. Check a model on your own work before you rely on it.

Method and measurements: [RESULTS.md](RESULTS.md).

## Tests

`python3 -m unittest discover -s tests` needs no model and no network.

MIT licence.
