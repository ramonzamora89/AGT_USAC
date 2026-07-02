"""Pipeline exploratorio de análisis SNA para AGT_USAC (versión anterior a
export_executive_json.py; se conserva como referencia, no se usa en el
sitio actual).

Hace 4 cosas:
1. Construye el grafo (red de followers/following + interacciones de comments/quotes).
2. Clasifica nodos en Medios / Usuarios / Desconocido (account_categories.csv
   como fuente confiable, más una clasificación aproximada por palabras
   clave en la biografía para el resto de la red).
3. Detecta cuentas sospechosas de bot: ratio friends/followers > 10:1, o
   out-degree alto con in-degree bajo.
4. Detecta comunidades (Label Propagation) y etiqueta narrativas por
   palabras clave, tanto para el subset de Medios como por clúster.
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd
from networkx.algorithms.community import label_propagation_communities

BASE = Path(__file__).resolve().parent.parent
DATASET = BASE / "Dataset"

# --- Narrativas: derivadas de un análisis de frecuencia de palabras sobre el
# corpus actual de Comments+Quotes (481 textos). El bucket de infraestructura
# queda deliberadamente incluido aunque hoy tenga poca cobertura, para
# rastrear su crecimiento a medida que se sume más data. Ajustar si no
# refleja lo que se está viendo cualitativamente. ---
NARRATIVES = {
    "Decepcion_Traicion_Politica": {
        "title": "Decepción y traición política (Arévalo / Semilla)",
        "keywords": ["arévalo", "arevalo", "bernardo", "bernie", "semilla", "tibio", "tibios",
                     "traidor", "traición", "decepción", "cobarde", "usurpador", "legitimidad", "exilio"],
    },
    "USAC_Fraude_Rectoria": {
        "title": "USAC: fraude y crisis de rectoría",
        "keywords": ["usac", "universidad", "estudiantes", "mazariegos", "rector", "fraude",
                     "elecciones", "consejo superior", "csu"],
    },
    "Pactos_y_Corrupcion": {
        "title": "Pactos y corrupción opaca",
        "keywords": ["corrup", "pacto", "cacif", "mordida", "cómplice", "negocio turbio"],
    },
    "Ana_Glenda_Tager": {
        "title": "Figura de Ana Glenda Tager",
        "keywords": ["tager", "glenda"],
    },
    "Plan_Infraestructura_Quinonez": {
        "title": "Plan de infraestructura / Ricardo Quiñonez",
        "keywords": ["quiñon", "quinon", "infraestructura", "aeropuerto", "carretera", "obra",
                     "contrato", "licitac", "presupuesto"],
    },
}

MEDIA_BIO_KEYWORDS = ["noticia", "diario", "canal", "radio", "medio de comunicaci",
                      "prensa", "periodis", "noticiero", "informativo", "redacción"]


def tag_narratives(text_lower: str) -> list[str]:
    return [key for key, info in NARRATIVES.items() if any(kw in text_lower for kw in info["keywords"])]


def load_account_categories() -> dict[str, str]:
    path = DATASET / "account_categories.csv"
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    df = df[df["categoria"] != "pendiente"]
    return {row.screen_name.lower(): row.categoria for row in df.itertuples()}


def build_graph(known_categories: dict[str, str]) -> nx.DiGraph:
    G = nx.DiGraph()

    # 1. Red de followers/following
    for f in glob.glob(str(DATASET / "Redes" / "**" / "*.csv"), recursive=True):
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        needed = {"type", "target_username", "screen_name"}
        if not needed.issubset(df.columns):
            continue
        has_bio_cols = {"description", "verified", "followers_count", "friends_count"}.issubset(df.columns)
        for row in df.itertuples():
            u1 = str(row.target_username).strip()
            u2 = str(row.screen_name).strip()
            if not u1 or not u2 or u1 == "nan" or u2 == "nan":
                continue

            if u2 not in G:
                followers = getattr(row, "followers_count", 0)
                friends = getattr(row, "friends_count", 0)
                desc = str(getattr(row, "description", "") or "") if has_bio_cols else ""
                verified = str(getattr(row, "verified", "")).lower() == "true" if has_bio_cols else False
                G.add_node(u2, followers=followers, friends=friends, description=desc, verified=verified)
            if u1 not in G:
                G.add_node(u1, followers=0, friends=0, description="", verified=False)

            if row.type == "follower":
                G.add_edge(u2, u1, weight=1, type="connection")
            else:
                G.add_edge(u1, u2, weight=1, type="connection")

    # 2. Interacciones (Comments + Quotes)
    for f in glob.glob(str(DATASET / "Comments" / "**" / "*.csv"), recursive=True) + \
             glob.glob(str(DATASET / "Quotes" / "**" / "*.csv"), recursive=True):
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        author_col = "author/screen_name" if "author/screen_name" in df.columns else "authorUsername"
        if author_col not in df.columns:
            continue
        mention_cols = [c for c in df.columns if ("user_mentions" in c and "screen_name" in c) or c == "inReplyToUsername"]
        for _, row in df.iterrows():
            author = row.get(author_col)
            if pd.isna(author):
                continue
            author = str(author).strip()
            if author not in G:
                G.add_node(author, followers=0, friends=0, description="", verified=False)
            for mc in mention_cols:
                mention = row.get(mc)
                if pd.isna(mention):
                    continue
                mention = str(mention).strip()
                if mention not in G:
                    G.add_node(mention, followers=0, friends=0, description="", verified=False)
                if G.has_edge(author, mention):
                    G[author][mention]["weight"] += 2
                else:
                    G.add_edge(author, mention, weight=2, type="interaction")

    # 3. Categoría por nodo: account_categories.csv (autoritativo) + palabras clave en bio
    for n, data in G.nodes(data=True):
        key = n.lower()
        if key in known_categories:
            data["categoria"] = known_categories[key]
            data["categoria_fuente"] = "confirmado"
            continue
        desc_lower = (data.get("description") or "").lower()
        if desc_lower and any(kw in desc_lower for kw in MEDIA_BIO_KEYWORDS):
            data["categoria"] = "Medios"
            data["categoria_fuente"] = "bio_palabra_clave"
        else:
            data["categoria"] = "Desconocido"
            data["categoria_fuente"] = "sin_datos"

    return G


def detect_bots(G: nx.DiGraph) -> pd.DataFrame:
    rows = []
    for n, data in G.nodes(data=True):
        in_deg, out_deg = G.in_degree(n), G.out_degree(n)
        friends = float(data.get("friends") or 0)
        followers = float(data.get("followers") or 0)
        ratio = friends / max(followers, 1)
        motivo = []
        if friends > 500 and ratio > 10:
            motivo.append("friends/followers>10:1")
        if out_deg > 15 and in_deg < 2:
            motivo.append("out_degree alto, in_degree bajo")
        if motivo:
            rows.append({
                "screen_name": n, "followers": followers, "friends": friends,
                "ratio_friends_followers": round(ratio, 1), "in_degree": in_deg, "out_degree": out_deg,
                "categoria": data.get("categoria"), "motivo": "; ".join(motivo),
            })
    return pd.DataFrame(rows).sort_values("ratio_friends_followers", ascending=False)


def detect_communities(G: nx.DiGraph) -> dict[str, int]:
    G_und = G.to_undirected()
    communities = list(label_propagation_communities(G_und))
    node_to_cluster = {}
    for i, comm in enumerate(communities):
        for node in comm:
            node_to_cluster[node] = i
    return node_to_cluster


def narratives_for_files(file_patterns: list[str], node_to_cluster: dict[str, int] | None = None):
    """Devuelve conteo de narrativas y, si se pasa node_to_cluster, conteo por clúster."""
    narrative_counts = Counter()
    cluster_narrative_counts: dict[int, Counter] = {}
    cluster_sizes: Counter = Counter()

    for pattern in file_patterns:
        for f in glob.glob(pattern, recursive=True):
            df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
            text_col = "text" if "text" in df.columns else "display_text"
            author_col = "author/screen_name" if "author/screen_name" in df.columns else "authorUsername"
            if text_col not in df.columns:
                continue
            for _, row in df.iterrows():
                text = row.get(text_col)
                if pd.isna(text):
                    continue
                tags = tag_narratives(str(text).lower())
                for t in tags:
                    narrative_counts[t] += 1
                if node_to_cluster is not None and author_col in df.columns:
                    author = row.get(author_col)
                    if pd.notna(author):
                        cluster = node_to_cluster.get(str(author).strip())
                        if cluster is not None:
                            cluster_sizes[cluster] += 1
                            for t in tags:
                                cluster_narrative_counts.setdefault(cluster, Counter())[t] += 1

    return narrative_counts, cluster_narrative_counts, cluster_sizes


def main():
    known_categories = load_account_categories()
    print(f"Categorías confirmadas cargadas: {len(known_categories)}")

    G = build_graph(known_categories)
    print(f"Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} relaciones")

    cat_counts = Counter(nx.get_node_attributes(G, "categoria").values())
    print("Distribución de categorías:", dict(cat_counts))

    bots_df = detect_bots(G)
    bots_df.to_csv(DATASET / "bot_candidates.csv", index=False, encoding="utf-8-sig")
    print(f"Cuentas sospechosas de bot: {len(bots_df)} ({len(bots_df)/max(G.number_of_nodes(),1)*100:.1f}% de la red)")

    node_to_cluster = detect_communities(G)
    n_clusters = len(set(node_to_cluster.values()))
    print(f"Clústeres detectados: {n_clusters}")

    # Narrativas en Medios (Comments/Quotes originados en tuits de cuentas de medios)
    media_counts, _, _ = narratives_for_files([
        str(DATASET / "Comments" / "Medios" / "*.csv"),
        str(DATASET / "Quotes" / "Medios" / "*.csv"),
    ])

    # Narrativas por clúster (todo el corpus)
    _, cluster_counts, cluster_sizes = narratives_for_files([
        str(DATASET / "Comments" / "**" / "*.csv"),
        str(DATASET / "Quotes" / "**" / "*.csv"),
    ], node_to_cluster=node_to_cluster)

    media_rows = [{"narrativa": k, "titulo": NARRATIVES[k]["title"], "menciones_en_medios": v}
                  for k, v in media_counts.most_common()]
    pd.DataFrame(media_rows).to_csv(DATASET / "narrativas_medios.csv", index=False, encoding="utf-8-sig")

    cluster_rows = []
    for cluster_id, counter in sorted(cluster_counts.items(), key=lambda kv: -cluster_sizes[kv[0]]):
        top_narrative = counter.most_common(1)[0][0] if counter else None
        members = [n for n, c in node_to_cluster.items() if c == cluster_id]
        top_actors = sorted(members, key=lambda n: G.in_degree(n), reverse=True)[:5]
        cluster_rows.append({
            "cluster_id": cluster_id,
            "tamano_cluster": len(members),
            "textos_con_narrativa": cluster_sizes[cluster_id],
            "narrativa_dominante": NARRATIVES[top_narrative]["title"] if top_narrative else "sin narrativa dominante",
            "top_actores": ", ".join(top_actors),
        })
    pd.DataFrame(cluster_rows).to_csv(DATASET / "narrativas_clusters.csv", index=False, encoding="utf-8-sig")

    node_rows = [{"screen_name": n, "categoria": d.get("categoria"), "categoria_fuente": d.get("categoria_fuente"),
                  "cluster": node_to_cluster.get(n), "in_degree": G.in_degree(n), "out_degree": G.out_degree(n)}
                 for n, d in G.nodes(data=True)]
    pd.DataFrame(node_rows).to_csv(DATASET / "node_categories.csv", index=False, encoding="utf-8-sig")

    print("\nArchivos generados en Dataset/: bot_candidates.csv, narrativas_medios.csv, narrativas_clusters.csv, node_categories.csv")


if __name__ == "__main__":
    main()
