import os
import time
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import GridSearchCV
from sklearn.svm import LinearSVC

PROC = os.path.join("data", "processed")
NAMES = ["Négatif", "Neutre", "Positif"]

train = pd.read_csv(os.path.join(PROC, "train.csv")).fillna("")
test = pd.read_csv(os.path.join(PROC, "test.csv")).fillna("")

vec = TfidfVectorizer(ngram_range=(1, 2), max_features=50000,
                      min_df=2, sublinear_tf=True)
X_train = vec.fit_transform(train["text"])
X_test = vec.transform(test["text"])
y_train, y_test = train["label"], test["label"]

# 1) Comparaison de plusieurs algorithmes
candidates = {
    "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
    "LinearSVC": LinearSVC(class_weight="balanced", C=0.5),
    "RandomForest": RandomForestClassifier(n_estimators=150, class_weight="balanced",
                                           n_jobs=-1, random_state=42),
}
for name, clf in candidates.items():
    t = time.time()
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    print(f"{name:20s} accuracy={accuracy_score(y_test, pred):.3f} "
          f"f1_macro={f1_score(y_test, pred, average='macro'):.3f} "
          f"({time.time() - t:.0f}s)")

# 2) Optimisation des hyperparamètres de la Logistic Regression
grid = GridSearchCV(
    LogisticRegression(max_iter=1000, class_weight="balanced"),
    param_grid={"C": [1, 5, 10, 20, 50]},
    scoring="f1_macro", cv=3, n_jobs=-1, verbose=1,
)
grid.fit(X_train, y_train)
best = grid.best_estimator_
print("Meilleurs paramètres :", grid.best_params_)

# 3) Évaluation finale sur le test set
pred = best.predict(X_test)
acc = accuracy_score(y_test, pred)
f1s = f1_score(y_test, pred, average=None)
print(classification_report(y_test, pred, target_names=NAMES, digits=3))

cm = confusion_matrix(y_test, pred)
plt.figure(figsize=(5.5, 4.5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=NAMES, yticklabels=NAMES)
plt.xlabel("Prédit")
plt.ylabel("Réel")
plt.title("Matrice de confusion (test)")
plt.tight_layout()
plt.savefig(os.path.join("reports", "confusion_matrix.png"), dpi=130)

# Temps d'inférence (médiane de 30 essais, batch de 50)
batch = test["text"].head(50).tolist()
times = []
for _ in range(30):
    t = time.perf_counter()
    best.predict(vec.transform(batch))
    times.append((time.perf_counter() - t) * 1000)
inf_ms = float(np.median(times))

print("\n--- Critères du sujet ---")
print(f"Accuracy >= 0.80      : {acc:.3f} -> {acc >= 0.80}")
print(f"F1 par classe > 0.75  : {np.round(f1s, 3)} -> {bool((f1s > 0.75).all())}")
print(f"Inférence < 100 ms    : {inf_ms:.1f} ms -> {inf_ms < 100}")

# 4) Sauvegarde
os.makedirs("models", exist_ok=True)
joblib.dump(best, os.path.join("models", "sentiment_model.joblib"))
joblib.dump(vec, os.path.join("models", "tfidf_vectorizer.joblib"))
print("Modèle et vectoriseur sauvegardés dans models/")