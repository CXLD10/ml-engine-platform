from __future__ import annotations

import pandas as pd

from app.ml.dataset_builder import FEATURE_COLUMNS


class Backtester:
    def run(self, dataset: pd.DataFrame) -> dict[str, float]:
        if dataset.empty:
            return {"trades": 0.0, "hit_rate": 0.0, "avg_return": 0.0}

        scores = dataset[FEATURE_COLUMNS].sum(axis=1)
        predictions = scores.apply(lambda x: 1 if x > 0 else -1)
        realized = dataset["target_next_return"].apply(lambda x: 1 if x > 0 else -1)
        hit_rate = float((predictions == realized).mean())
        strat_return = float((predictions * dataset["target_next_return"]).mean())
        return {"trades": float(len(dataset)), "hit_rate": hit_rate, "avg_return": strat_return}
