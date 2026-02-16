from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LinearRegressor:
    fit_intercept: bool = True
    l2_alpha: float = 1e-6

    def fit(self, x: np.ndarray, y: np.ndarray) -> "LinearRegressor":
        x_mat = x.astype(float)
        if self.fit_intercept:
            x_mat = np.column_stack([np.ones(len(x_mat)), x_mat])

        ident = np.eye(x_mat.shape[1]) * self.l2_alpha
        self._coef = np.linalg.pinv(x_mat.T @ x_mat + ident) @ x_mat.T @ y
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        x_mat = x.astype(float)
        if self.fit_intercept:
            x_mat = np.column_stack([np.ones(len(x_mat)), x_mat])
        return x_mat @ self._coef
