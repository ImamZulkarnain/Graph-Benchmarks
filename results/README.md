# Generated results

This folder initially contains only this explanation in a fresh clone because
generated outputs are excluded from Git.

- `python main.py prepare` creates `dataset_properties/` with the subgraph properties and summary tables.
- `python main.py benchmark` creates a new `benchmark_<timestamp>/` with measurements and metadata.
- `python main.py plot results/benchmark_<timestamp>` adds plots and summaries to that run.
- `python main.py` performs all three steps.

The prepared graph files are kept separately in `data/prepared/` and included in Git.
