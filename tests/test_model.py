"""Tests du modèle (phase 7 : performance, cas limites, temps d'inférence)."""
import glob
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "sentiment_model.joblib"
VEC_PATH = ROOT / "models" / "tfidf_vectorizer.joblib"


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def vectorizer():
    return joblib.load(VEC_PATH)


def predict(model, vectorizer, texts):
    return model.predict(vectorizer.transform(texts))


# ---------- Performance sur le jeu de test ----------
def _load_test_set():
    files = glob.glob(str(ROOT / "data" / "processed" / "*test*.csv"))
    if not files:
        pytest.skip("Fichier de test introuvable dans data/processed/ (adapter le motif)")
    df = pd.read_csv(files[0]).dropna(subset=["text", "label"])
    return df["text"].astype(str), df["label"].astype(int)


def test_accuracy_on_test_set(model, vectorizer):
    X, y = _load_test_set()
    acc = accuracy_score(y, predict(model, vectorizer, X))
    print(f"\nAccuracy : {acc:.3f}")
    assert acc >= 0.80


def test_f1_per_class(model, vectorizer):
    X, y = _load_test_set()
    y_pred = predict(model, vectorizer, X)
    f1s = f1_score(y, y_pred, average=None, labels=[-1, 0, 1])
    print(f"\nF1 (négatif, neutre, positif) : {np.round(f1s, 3)}")
    assert (f1s > 0.75).all()


# ---------- Cas limites ----------
EDGE_CASES = [
    "",                                  # vide
    "a",                                 # très court
    "ok",
    "love " * 1000,                      # très long
    "😍😍😍🔥🔥",                          # emojis seuls
    "I love this 😍 so good",            # texte + emojis
    "هذا الفيديو رائع جدا",               # arabe
    "Super vidéo, j'adore ! I love it",  # mélange français/anglais
    "2:05",                              # timestamp seul
    "http://example.com @user #tag",     # URL, mention, hashtag
]


@pytest.mark.parametrize("text", EDGE_CASES)
def test_edge_cases_do_not_crash(model, vectorizer, text):
    pred = predict(model, vectorizer, [text])
    assert len(pred) == 1
    assert int(pred[0]) in (-1, 0, 1)


# ---------- Temps d'inférence ----------
def test_inference_time_batch_50(model, vectorizer):
    texts = ["this video is really great and I love it"] * 50
    predict(model, vectorizer, texts)  # échauffement
    start = time.perf_counter()
    predict(model, vectorizer, texts)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\nInférence batch de 50 : {elapsed_ms:.2f} ms")
    assert elapsed_ms < 100