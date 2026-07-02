"""Extrae el listado de usuarios (screen_names) únicos a partir de los
datasets de Comments y Quotes, para usarlos como input del actor de
extracción de perfiles en Apify.

Incluye tanto a quienes comentaron/citaron como a los autores de las
publicaciones originales (recuperados vía el primer @mention de cada
respuesta en Comments, y cruzando parentTweetId de Quotes contra esos
mismos tuits).
"""
from collections import Counter

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATASET = BASE / "Dataset"

COMMENTS_COLS = {"screen_name": "author/screen_name", "name": "author/name"}
QUOTES_COLS = {"screen_name": "authorUsername", "name": "authorName"}


def load(subdir: str, cols: dict, fuente: str) -> list[pd.DataFrame]:
    frames = []
    for csv_path in sorted((DATASET / subdir).rglob("*.csv")):
        df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)
        if cols["screen_name"] not in df.columns:
            print(f"  [aviso] {csv_path.name}: sin columna '{cols['screen_name']}', se omite")
            continue
        sub = df[[cols["screen_name"], cols["name"]]].copy()
        sub.columns = ["screen_name", "name"]
        sub["fuente"] = fuente
        sub["origen_categoria"] = csv_path.parent.name  # Medios / Usuarios (del tuit original)
        sub["archivo"] = csv_path.name
        frames.append(sub)
    return frames


def resolve_original_authors() -> list[pd.DataFrame]:
    """Recupera autores de tuits originales vía el primer @mention de cada
    respuesta en Comments (una fila por conversation_id, voto de mayoría),
    y los reutiliza para los parentTweetId de Quotes que coincidan."""
    tweet_author: dict[str, tuple[str, str, str]] = {}  # tweet_id -> (screen_name, name, origen_categoria)

    for csv_path in sorted((DATASET / "Comments").rglob("*.csv")):
        df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)
        needed = {"conversation_id", "entities/user_mentions/0/screen_name", "entities/user_mentions/0/name"}
        if not needed.issubset(df.columns):
            continue
        origen_categoria = csv_path.parent.name
        for cid, group in df.groupby("conversation_id"):
            mentions = group["entities/user_mentions/0/screen_name"].dropna().tolist()
            if not mentions:
                continue
            top_screen_name, _ = Counter(mentions).most_common(1)[0]
            top_name = group.loc[
                group["entities/user_mentions/0/screen_name"] == top_screen_name,
                "entities/user_mentions/0/name",
            ].iloc[0]
            tweet_author[cid] = (top_screen_name, top_name, origen_categoria)

    unresolved_parents = set()
    for csv_path in sorted((DATASET / "Quotes").rglob("*.csv")):
        df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)
        if "parentTweetId" not in df.columns:
            continue
        for pid in df["parentTweetId"].dropna().unique():
            if pid not in tweet_author:
                unresolved_parents.add(pid)

    if unresolved_parents:
        print(f"  [aviso] {len(unresolved_parents)} parentTweetId de Quotes sin autor original resuelto: {sorted(unresolved_parents)}")

    rows = [
        {"screen_name": sn, "name": name, "fuente": "autor_original", "origen_categoria": cat, "archivo": ""}
        for sn, name, cat in tweet_author.values()
    ]
    return [pd.DataFrame(rows)] if rows else []


def main():
    frames = (
        load("Comments", COMMENTS_COLS, "comments")
        + load("Quotes", QUOTES_COLS, "quotes")
        + resolve_original_authors()
    )
    all_df = pd.concat(frames, ignore_index=True)

    all_df["screen_name"] = all_df["screen_name"].str.strip()
    all_df = all_df[all_df["screen_name"].notna() & (all_df["screen_name"] != "")]

    agg = (
        all_df.groupby(all_df["screen_name"].str.lower())
        .agg(
            screen_name=("screen_name", "first"),
            name=("name", "first"),
            apariciones=("screen_name", "count"),
            fuentes=("fuente", lambda x: ",".join(sorted(set(x)))),
            categorias_origen=("origen_categoria", lambda x: ",".join(sorted(set(x)))),
        )
        .reset_index(drop=True)
        .sort_values("apariciones", ascending=False)
    )

    out_csv = DATASET / "unique_users.csv"
    agg.to_csv(out_csv, index=False, encoding="utf-8-sig")

    out_txt = DATASET / "apify_users_list.txt"
    out_txt.write_text("\n".join(agg["screen_name"]) + "\n", encoding="utf-8")

    print(f"\nUsuarios únicos encontrados: {len(agg)}")
    print(f"CSV detallado: {out_csv}")
    print(f"Listado plano (input Apify): {out_txt}")


if __name__ == "__main__":
    main()
