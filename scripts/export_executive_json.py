"""Genera scrollytelling-site/visuals/executive_network.json: un único JSON
liviano con nodes/links/narratives/stats, precalculado para que el sitio
cargue y anime la red sin trabarse y pueda hacer zoom fluido a cada clúster.

Las narrativas se arman por palabra clave (Arévalo/Semilla, USAC, Pactos y
corrupción, Ana Glenda Tager, Plan de infraestructura/Quiñonez), excepto
"Medios", que se arma por identidad de cuenta: los 7 medios confirmados en
account_categories.csv. El resto de las cuentas de la red se agrupa solo por
narrativa, sin clasificación individual de medio/usuario.
"""
import glob
import json
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd
from networkx.algorithms.community import label_propagation_communities

BASE = Path(__file__).resolve().parent.parent
DATASET = BASE / "Dataset"
OUT_DIR = BASE / "scrollytelling-site" / "visuals"

# El JSON que consume el sitio debe quedar liviano: se recorta la red completa
# (55k+ nodos) a un subconjunto visual. Siempre se incluyen los nodos
# relevantes para la historia (medios, actores por narrativa, top hubs,
# muestra de cuentas inorgánicas) más los de mayor centralidad para dar
# textura de red en las vistas generales.
TOP_BY_INDEGREE = 1500
BOT_SAMPLE_SIZE = 300

NARRATIVES = {
    "Decepcion_Traicion_Politica": {
        "title": "Decepción y traición política",
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


def load_confirmed_media() -> set[str]:
    df = pd.read_csv(DATASET / "account_categories.csv", encoding="utf-8-sig", dtype=str)
    return set(df.loc[df["categoria"] == "Medios", "screen_name"].str.lower())


def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()

    for f in glob.glob(str(DATASET / "Redes" / "**" / "*.csv"), recursive=True):
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        if not {"type", "target_username", "screen_name"}.issubset(df.columns):
            continue
        for row in df.itertuples():
            u1, u2 = str(row.target_username).strip(), str(row.screen_name).strip()
            if not u1 or not u2 or u1 == "nan" or u2 == "nan":
                continue
            if u2 not in G:
                G.add_node(u2, followers=getattr(row, "followers_count", 0) or 0,
                           friends=getattr(row, "friends_count", 0) or 0, narrativas=set())
            if u1 not in G:
                G.add_node(u1, followers=0, friends=0, narrativas=set())
            if row.type == "follower":
                G.add_edge(u2, u1, weight=1, type="connection")
            else:
                G.add_edge(u1, u2, weight=1, type="connection")

    for f in glob.glob(str(DATASET / "Comments" / "**" / "*.csv"), recursive=True) + \
             glob.glob(str(DATASET / "Quotes" / "**" / "*.csv"), recursive=True):
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        author_col = "author/screen_name" if "author/screen_name" in df.columns else "authorUsername"
        text_col = "text" if "text" in df.columns else "display_text"
        if author_col not in df.columns or text_col not in df.columns:
            continue
        mention_cols = [c for c in df.columns if ("user_mentions" in c and "screen_name" in c) or c == "inReplyToUsername"]

        for _, row in df.iterrows():
            author = row.get(author_col)
            if pd.isna(author):
                continue
            author = str(author).strip()
            if author not in G:
                G.add_node(author, followers=0, friends=0, narrativas=set())

            text_lower = str(row.get(text_col) or "").lower()
            for key, info in NARRATIVES.items():
                if any(kw in text_lower for kw in info["keywords"]):
                    G.nodes[author]["narrativas"].add(key)

            for mc in mention_cols:
                mention = row.get(mc)
                if pd.isna(mention):
                    continue
                mention = str(mention).strip()
                if mention not in G:
                    G.add_node(mention, followers=0, friends=0, narrativas=set())
                if G.has_edge(author, mention):
                    G[author][mention]["weight"] += 2
                else:
                    G.add_edge(author, mention, weight=2, type="interaction")

    return G


def main():
    confirmed_media = load_confirmed_media()
    G = build_graph()
    print(f"Grafo: {G.number_of_nodes()} nodos, {G.number_of_edges()} relaciones")

    G_und = G.to_undirected()
    communities = list(label_propagation_communities(G_und))
    for i, comm in enumerate(communities):
        for node in comm:
            G.nodes[node]["group"] = i

    centrality_in = {n: G.in_degree(n) for n in G.nodes()}
    top_hubs = sorted(centrality_in, key=centrality_in.get, reverse=True)[:20]

    all_nodes_data = {}
    inorganic_nodes = []
    organic_nodes = []

    for n, data in G.nodes(data=True):
        in_deg, out_deg = G.in_degree(n), G.out_degree(n)
        friends = float(data.get("friends") or 0)
        followers = float(data.get("followers") or 1)
        is_inorganic = (friends > 500 and (friends / max(followers, 1)) > 10) or (out_deg > 15 and in_deg < 2)
        node_type = "inorganic" if is_inorganic else "organic"
        (inorganic_nodes if is_inorganic else organic_nodes).append(n)

        all_nodes_data[n] = {
            "id": n,
            "group": data.get("group", 0),
            "type": node_type,
            "val": in_deg + 1,
            "es_medio": n.lower() in confirmed_media,
            "label": n if (n in top_hubs or n.lower() in confirmed_media) else "",
            "_out_deg": out_deg,
        }

    bot_targets = Counter()
    for b in inorganic_nodes:
        for _, target in G.out_edges(b):
            if G.nodes[target].get("group") is not None and target not in inorganic_nodes:
                bot_targets[target] += 1
    top_bot_targets = bot_targets.most_common(10)

    narrative_results = {}
    for key, info in NARRATIVES.items():
        sub_nodes = [n for n in G.nodes() if key in G.nodes[n].get("narrativas", set())]
        top_influencers = sorted(sub_nodes, key=lambda n: G.in_degree(n), reverse=True)[:8]
        actors_data = [{"id": a, "type": "inorganic" if a in inorganic_nodes else "organic"} for a in top_influencers]
        narrative_results[key] = {"title": info["title"], "top_actors": actors_data, "node_count": len(sub_nodes)}

    # Narrativa "Medios": no por palabras clave, por identidad de cuenta confirmada
    media_nodes = [n for n in G.nodes() if n.lower() in confirmed_media]
    narrative_results["Medios"] = {
        "title": "Medios de comunicación",
        "top_actors": [{"id": a, "type": "inorganic" if a in inorganic_nodes else "organic"} for a in media_nodes],
        "node_count": len(media_nodes),
    }

    # Muestra de cuentas inorgánicas para mostrar en el sitio: las más activas
    # (mayor out-degree), no una muestra alfabética arbitraria.
    bot_sample = sorted(inorganic_nodes, key=lambda n: all_nodes_data[n]["_out_deg"], reverse=True)[:BOT_SAMPLE_SIZE]

    # --- Recorte del grafo para el JSON del sitio ---
    # Sin esto, el JSON serializa la red completa (55k+ nodos, 12MB+), que es
    # exactamente lo que se quiere evitar con un archivo "ejecutivo" liviano.
    important = set(top_hubs) | set(media_nodes) | set(bot_sample)
    for info in narrative_results.values():
        important.update(a["id"] for a in info["top_actors"])

    by_indegree = sorted(G.nodes(), key=lambda n: centrality_in[n], reverse=True)[:TOP_BY_INDEGREE]
    keep = important | set(by_indegree)

    nodes_data = [{k: v for k, v in all_nodes_data[n].items() if not k.startswith("_")} for n in keep]
    links_data = [
        {"source": u, "target": v, "value": int(d.get("weight", 1))}
        for u, v, d in G.edges(data=True)
        if u in keep and v in keep
    ]

    final_json = {
        "nodes": nodes_data,
        "links": links_data,
        "narratives": narrative_results,
        "stats": {
            "total_nodes": len(G.nodes()),
            "total_links": G.number_of_edges(),
            "organic_count": len(organic_nodes),
            "inorganic_count": len(inorganic_nodes),
            "bot_percentage": round((len(inorganic_nodes) / len(G.nodes())) * 100, 2) if G.number_of_nodes() else 0,
            "top_bot_targets": [{"id": t, "count": c} for t, c in top_bot_targets],
            "all_bots": sorted(bot_sample)[:100],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "executive_network.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False)

    print(f"Red completa: {G.number_of_nodes()} nodos, {G.number_of_edges()} relaciones.")
    print(f"JSON del sitio (recortado): {len(nodes_data)} nodos, {len(links_data)} relaciones "
          f"({out_path.stat().st_size / 1024:.0f} KB).")
    print(f"Bots totales: {len(inorganic_nodes)} ({final_json['stats']['bot_percentage']}%). "
          f"Muestra visual de bots: {len(bot_sample)}.")
    for key, info in narrative_results.items():
        print(f"  {key}: {info['node_count']} cuentas")
    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()
