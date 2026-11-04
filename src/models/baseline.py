import os
import time
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

PROC = os.path.join("data", "processed")

train = pd.read_csv(os.path.join(PROC, "train.csv")).fillna("")
test = pd.read_csv(os.path.join(PROC, "test.csv")).fillna("")

# Texte -> vecteurs TF-IDF (mots seuls et paires de mots)
vec = TfidfVectorizer(ngram_range=(1, 2), max_features=50000,
                      min_df=2, sublinear_tf=True)
X_train = vec.fit_transform(train["text"])   # on apprend le vocabulaire sur le train
X_test = vec.transform(test["text"])         # on applique sur le test (sans réapprendre)
print("Nombre de features :", X_train.shape[1])

# Entraînement
model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(X_train, train["label"])

# Évaluation
pred = model.predict(X_test)
print("Accuracy :", round(accuracy_score(test["label"], pred), 4))
print(classification_report(test["label"], pred,
                            target_names=["Négatif", "Neutre", "Positif"], digits=3))

# Temps d'inférence pour 50 commentaires (vectorisation + prédiction)
batch = test["text"].head(50).tolist()
t = time.perf_counter()
model.predict(vec.transform(batch))
print("Inférence batch de 50 :", round((time.perf_counter() - t) * 1000, 1), "ms")