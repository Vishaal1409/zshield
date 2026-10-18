# data/ (not committed)

Large data files stay out of git. Put your local copy here.

1. `paysim.csv`: the raw PaySim file (Kaggle `ealaxi/paysim1`, or the Hugging Face mirror
   `theman10/paysim`, same 493,534,783-byte file). Shared on Google Drive.
2. Then run, from the repo root (about 1 minute):
   ```bash
   python -m features.prepare_data data/paysim.csv
   ```
   This writes `train.parquet`, `val.parquet` and `test.parquet` here (raw columns, all features, `isFraud`),
   and the committed demo files in `docs/demo/` (demo stream, 3 stories, data summary).

EDA charts: `python -m features.make_eda_notebook` (writes `features/eda.ipynb` and `docs/eda/*.png`).
Details and limitations: `features/data_card.md`.
