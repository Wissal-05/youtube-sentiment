# Rapport de performance du modèle

Modèle : TF-IDF + Logistic Regression (scikit-learn). Fichiers : `models/sentiment_model.joblib` et `models/tfidf_vectorizer.joblib`.

## Données

- Source : dataset Reddit Sentiment Analysis (37 249 commentaires bruts, labels -1 / 0 / 1)
- Après nettoyage et suppression des doublons : 36 493 lignes
- Split : 80 % / 20 % stratifié, `random_state=42` (29 194 entraînement, 7 299 test)

## Configuration

| Élément | Valeur |
|---|---|
| Vectoriseur | TfidfVectorizer : n-grammes (1, 2), `max_features=50000`, `min_df=2`, `sublinear_tf=True` |
| Déséquilibre des classes | `class_weight="balanced"` |
| Recherche d'hyperparamètres | GridSearchCV, `C` dans [1, 5, 10, 20, 50], `cv=3`, `scoring="f1_macro"` |
| Meilleur paramètre | `C = 50` (en bord de grille) |

## Comparaison des algorithmes (jeu de test)

| Algorithme | Accuracy | F1 macro |
|---|---|---|
| Logistic Regression (défaut) | 0,849 | 0,839 |
| LinearSVC | 0,876 | 0,864 |
| Random Forest | 0,796 | 0,765 |
| **Logistic Regression optimisée (C = 50)** | **0,884** | **0,873** |

## Modèle retenu

| Classe | F1-score |
|---|---|
| Négatif (-1) | 0,805 |
| Neutre (0) | 0,918 |
| Positif (1) | 0,895 |

## Critères du sujet

| Critère | Objectif | Résultat | Validé |
|---|---|---|---|
| Accuracy | ≥ 80 % | 88,4 % | Oui |
| F1 par classe | > 0,75 | 0,805 à 0,918 | Oui |
| Inférence, batch de 50 | < 100 ms | environ 2 ms | Oui |

## Visualisations

- Analyse exploratoire : `reports/eda.png`
- Matrice de confusion : `reports/confusion_matrix.png`

## Limites

- Entraîné sur du texte Reddit en anglais : les autres langues sont mal classées.
- TF-IDF suit le vocabulaire plutôt que le sens (ironie, spam, négations).
- `C = 50` est au bord de la grille : une grille plus large pourrait améliorer légèrement le score.

## Reproduire

```powershell
python -m src.data.download_data
python -m src.data.preprocess
python -m src.models.train
pytest -v -s
```