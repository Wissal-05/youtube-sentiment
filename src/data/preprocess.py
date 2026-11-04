import os
import matplotlib
matplotlib.use("Agg")  # pas de fenêtre, on sauvegarde l'image
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.model_selection import train_test_split

from src.utils.text_cleaning import clean_text

RAW = os.path.join("data", "raw", "reddit.csv")
PROC = os.path.join("data", "processed")
SEED = 42


def main():
    # 1) Chargement et renommage des colonnes (le sujet demande 'text' et 'label')
    df = pd.read_csv(RAW).rename(columns={"clean_comment": "text", "category": "label"})
    print("Brut :", len(df), "lignes")

    # 2) Nettoyage
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    df["text"] = df["text"].astype(str).map(clean_text)
    df = df[df["text"].str.len() > 0].drop_duplicates(subset="text")
    print("Après nettoyage :", len(df), "lignes")

    # 3) Analyse exploratoire
    print("Classes (%) :")
    print((df["label"].value_counts(normalize=True).sort_index() * 100).round(1))
    lengths = df["text"].str.split().str.len()
    print("Longueur des textes (mots) :")
    print(lengths.describe().round(1))

    os.makedirs("reports", exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    counts = df["label"].value_counts().sort_index()
    ax[0].bar(["Négatif", "Neutre", "Positif"], counts.values,
              color=["#e74c3c", "#95a5a6", "#2ecc71"])
    ax[0].set_title("Distribution des classes")
    ax[1].hist(lengths.clip(upper=200), bins=40, color="#3498db")
    ax[1].set_title("Longueur des textes (mots, tronquée à 200)")
    plt.tight_layout()
    plt.savefig(os.path.join("reports", "eda.png"), dpi=130)

    # 4) Split train/test : 80/20, stratifié, graine fixe = reproductible
    train, test = train_test_split(df, test_size=0.2, random_state=SEED,
                                   stratify=df["label"])
    os.makedirs(PROC, exist_ok=True)
    train[["text", "label"]].to_csv(os.path.join(PROC, "train.csv"), index=False)
    test[["text", "label"]].to_csv(os.path.join(PROC, "test.csv"), index=False)
    print("Train :", len(train), "| Test :", len(test))


if __name__ == "__main__":
    main()