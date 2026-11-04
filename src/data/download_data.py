import os
import requests
import pandas as pd

URL = ("https://raw.githubusercontent.com/Himanshu-1703/"
       "reddit-sentiment-analysis/refs/heads/main/data/reddit.csv")
OUT = os.path.join("data", "raw", "reddit.csv")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    with open(OUT, "wb") as f:
        f.write(r.content)

    df = pd.read_csv(OUT)
    print("Nombre de commentaires :", len(df))
    print("Distribution des labels :")
    print(df["category"].value_counts())


if __name__ == "__main__":
    main()