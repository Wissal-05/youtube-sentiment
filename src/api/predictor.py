import os
from collections import Counter

import joblib
import numpy as np

from src.utils.text_cleaning import clean_text

NAMES = {-1: "negative", 0: "neutral", 1: "positive"}


class SentimentPredictor:
    def __init__(self, model_dir="models"):
        self.model = joblib.load(os.path.join(model_dir, "sentiment_model.joblib"))
        self.vectorizer = joblib.load(os.path.join(model_dir, "tfidf_vectorizer.joblib"))
        self.classes = [int(c) for c in self.model.classes_]

    def predict_batch(self, comments):
        cleaned = [clean_text(c) for c in comments]
        valid = [i for i, c in enumerate(cleaned) if c]   # textes non vides
        results = [None] * len(comments)

        if valid:
            X = self.vectorizer.transform([cleaned[i] for i in valid])
            proba = self.model.predict_proba(X)
            for row, i in zip(proba, valid):
                k = int(np.argmax(row))
                results[i] = (self.classes[k], float(row[k]), row)

        predictions = []
        for text, res in zip(comments, results):
            if res is None:  # vide après nettoyage (ex. uniquement des emojis)
                label, conf = 0, 0.0
                probs = {NAMES[c]: (1.0 if c == 0 else 0.0) for c in self.classes}
            else:
                label, conf, row = res
                probs = {NAMES[c]: round(float(p), 4) for c, p in zip(self.classes, row)}
            predictions.append({"text": text, "label": label,
                                "sentiment": NAMES[label],
                                "confidence": round(conf, 4),
                                "probabilities": probs})

        counts = Counter(p["sentiment"] for p in predictions)
        counts = {n: counts.get(n, 0) for n in ("positive", "neutral", "negative")}
        total = len(predictions)
        stats = {
            "total": total,
            "counts": counts,
            "percentages": {k: round(100 * v / total, 1) for k, v in counts.items()},
            "average_confidence": round(float(np.mean([p["confidence"] for p in predictions])), 4),
            "dominant_sentiment": max(counts, key=counts.get),
        }
        return predictions, stats