from __future__ import annotations

import math
from functools import lru_cache

import numpy as np


FEATURE_NAMES = [
    "glucose",
    "systolic",
    "weight_gain",
    "swelling",
    "tired",
    "appetite",
    "breath",
    "dizziness",
    "nausea",
    "edema",
    "confusion",
    "dialysis_day",
    "missed_meds",
    "salty_food",
    "fluid_extra",
    "sweet_food",
    "photo_quality_bad",
    "face_color_change",
]


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(values, -40, 40)))


def _normalize(raw: np.ndarray) -> np.ndarray:
    normalized = raw.astype(float).copy()
    normalized[:, 0] = (normalized[:, 0] - 120) / 90
    normalized[:, 1] = (normalized[:, 1] - 130) / 45
    normalized[:, 2] = normalized[:, 2] / 3
    normalized[:, 3:11] = normalized[:, 3:11] / 3
    normalized[:, 12] = normalized[:, 12] / 3
    normalized[:, 13:16] = normalized[:, 13:16] / 3
    return normalized


def _synthetic_rule_score(x: np.ndarray) -> float:
    glucose = x[0]
    systolic = x[1]
    weight_gain = x[2]
    swelling, tired, appetite, breath, dizziness, nausea, edema, confusion = x[3:11]
    dialysis_day = x[11]
    missed_meds = x[12]
    salty_food, fluid_extra, sweet_food = x[13:16]
    photo_quality_bad = x[16]
    face_color_change = x[17]

    score = 0.0
    score += breath * 16 + confusion * 18 + swelling * 9 + edema * 10
    score += dizziness * 8 + nausea * 6 + tired * 6 + appetite * 4

    if glucose < 70 or glucose > 300:
        score += 25
    elif glucose > 250:
        score += 18
    elif glucose > 180:
        score += 10

    if systolic >= 180:
        score += 24
    elif systolic >= 160:
        score += 14
    elif systolic <= 90:
        score += 18

    if weight_gain >= 3:
        score += 20
    elif weight_gain >= 2:
        score += 10

    score += dialysis_day * 4
    score += min(18, missed_meds * 9)
    score += salty_food * 5 + fluid_extra * 6 + sweet_food * 6
    score += photo_quality_bad * 4 + face_color_change * 6
    return min(100, score)


def _make_synthetic_dataset(seed: int = 20260615, rows: int = 6000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    data = []
    labels = []

    for _ in range(rows):
        glucose = float(np.clip(rng.normal(145, 65), 45, 420))
        systolic = float(np.clip(rng.normal(138, 32), 75, 230))
        weight_gain = float(np.clip(rng.gamma(2.0, 0.8), 0, 6))
        symptoms = rng.choice([0, 1, 2, 3], size=8, p=[0.62, 0.23, 0.11, 0.04]).astype(float)
        dialysis_day = float(rng.random() < 0.22)
        missed_meds = float(rng.choice([0, 1, 2, 3], p=[0.75, 0.16, 0.07, 0.02]))
        diet = rng.choice([0, 1, 2, 3], size=3, p=[0.58, 0.25, 0.12, 0.05]).astype(float)
        photo_quality_bad = float(rng.random() < 0.12)
        face_color_change = float(rng.random() < 0.16)

        row = np.array(
            [
                glucose,
                systolic,
                weight_gain,
                *symptoms,
                dialysis_day,
                missed_meds,
                *diet,
                photo_quality_bad,
                face_color_change,
            ],
            dtype=float,
        )
        risk = _synthetic_rule_score(row)
        noisy_risk = risk + rng.normal(0, 6)
        label = 1.0 if noisy_risk >= 45 else 0.0
        data.append(row)
        labels.append(label)

    return np.vstack(data), np.array(labels)


@lru_cache(maxsize=1)
def train_model() -> tuple[np.ndarray, float]:
    x_raw, y = _make_synthetic_dataset()
    x = _normalize(x_raw)
    x = np.column_stack([np.ones(len(x)), x])
    weights = np.zeros(x.shape[1])
    lr = 0.08
    reg = 0.003

    for _ in range(900):
        pred = _sigmoid(x @ weights)
        grad = (x.T @ (pred - y)) / len(y)
        grad[1:] += reg * weights[1:]
        weights -= lr * grad

    logits = x @ weights
    probabilities = _sigmoid(logits)
    loss = float(-(y * np.log(probabilities + 1e-9) + (1 - y) * np.log(1 - probabilities + 1e-9)).mean())
    return weights, loss


def predict_ai_risk(features: dict) -> dict:
    weights, loss = train_model()
    row = np.array([[float(features[name]) for name in FEATURE_NAMES]], dtype=float)
    x = _normalize(row)
    x = np.column_stack([np.ones(len(x)), x])
    probability = float(_sigmoid(x @ weights)[0])
    score = int(round(probability * 100))

    if score >= 70:
        level = "AI提示高风险"
    elif score >= 40:
        level = "AI提示需要注意"
    else:
        level = "AI提示较稳定"

    return {
        "score": score,
        "probability": probability,
        "level": level,
        "training_loss": round(loss, 4),
        "model": "synthetic_logistic_regression_v1",
    }


def model_card_text() -> str:
    return (
        "模型原型：逻辑回归。训练资料：合成的临床规则数据，不含真实人脸照片。"
        "用途：辅助排序风险，不用于诊断。照片只用于和患者自己的基准照片比较。"
    )
