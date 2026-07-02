import pandas as pd
import networkx as nx
from networkx.algorithms.community import label_propagation_communities
import glob
import json
import os
import re
from collections import Counter

print("Iniciando procesamiento avanzado de la red y narrativas...")

# Definición de Narrativas
narratives_def = {
    "Pactos_y_Corrupcion": {
        "title": "Pactos y corrupción opaca",
        "keywords": ['corrup', 'negocio', 'pacto', 'cacif', 'unionismo', 'mordida', 'pisto', 'trancera', 'cómplice', 'pago'],
        "nodes": set()
    },
    "Ineficiencia_Tecnica": {
        "title": "Ineficiencia y crítica técnica",
        "keywords": ['metro', 'teleférico', 'turístico', 'mamarrachada', 'movilidad', 'columpio', 'transporte', 'capacidad', 'aerómetro', 'técnico'],
        "nodes": set()
    },
    "Decepcion_Politica": {
        "title": "Decepción y traición política",
        "keywords": ['arévalo', 'bernardo', 'semilla', 'voto', 'traición', 'decepción', 'tibieza', 'votos', 'exilio'],
        "nodes": set()
    },
    "Gestion_Municipal": {
        "title": "Crítica a la gestión municipal",
        "keywords": ['quiñones', 'muni', 'guate', 'alcalde', 'gestión', 'hoyos', 'jardines', 'años', '40'],
        "nodes": set()
    }
}

G = nx.DiGraph()

# 1. Cargar Redes de Apify
redes_files = glob.glob('Dataset/Redes/*.csv')
for f in redes_files:
    try:
        df = pd.read_csv(f)
        for _, row in df.iterrows():
            u1, u2 = str(row['target_username']).strip(), str(row['screen_name']).strip()
            if u2 not in G: G.add_node(u2, followers=row.get('followers_count', 0), friends=row.get('friends_count', 0), mentions_tager=0, mentions_aero=0)
            if u1 not in G: G.add_node(u1, followers=0, friends=0, mentions_tager=0, mentions_aero=0)
            G.add_edge(u2, u1, type='connection')
    except: pass

# 2. Cargar Interacciones
comments_files = glob.glob('Dataset/Comments/*.csv')
quotes_files = glob.glob('Dataset/Quotes/*.csv')

tager_pattern = re.compile(r'tager|glenda|ana glenda', re.I)
aero_pattern = re.compile(r'aerometro|teleferico|transporte', re.I)

aerometro_only_corpus = []

for f in comments_files + quotes_files:
    try:
        df = pd.read_csv(f)
        author_col = 'author/screen_name' if 'author/screen_name' in df.columns else 'authorUsername'
        text_col = 'text' if 'text' in df.columns else 'display_text'
        
        for _, row in df.iterrows():
            author = row[author_col]
            text = str(row[text_col])
            text_lower = text.lower()
            if pd.isna(author): continue
            
            if author not in G: G.add_node(author, followers=0, friends=0, mentions_tager=0, mentions_aero=0)
            if tager_pattern.search(text_lower): G.nodes[author]['mentions_tager'] += 1
            if aero_pattern.search(text_lower): G.nodes[author]['mentions_aero'] += 1
            if aero_pattern.search(text_lower) and not tager_pattern.search(text_lower):
                aerometro_only_corpus.append(text)

            for n_id, n_info in narratives_def.items():
                if any(kw in text_lower for kw in n_info['keywords']):
                    n_info['nodes'].add(author)

            mention_cols = [c for c in df.columns if ('user_mentions' in c and 'screen_name' in c) or c == 'inReplyToUsername']
            for mc in mention_cols:
                mention = row[mc]
                if not pd.isna(mention):
                    if mention not in G: G.add_node(mention, followers=0, friends=0, mentions_tager=0, mentions_aero=0)
                    G.add_edge(author, mention, weight=2, type='interaction')
    except: pass

# 3. Métricas
print("Calculando comunidades y métricas finales...")
G_undirected = G.to_undirected()
communities = list(label_propagation_communities(G_undirected))
for i, comm in enumerate(communities):
    for node in comm: G.nodes[node]['group'] = i

# Centralidad para labels (Top 20 hubs globales)
centrality = nx.in_degree_centrality(G)
top_hubs = sorted(centrality, key=centrality.get, reverse=True)[:20]

# 4. Clasificación y Estadísticas
nodes_data = []
inorganic_nodes = []
organic_nodes = []

for n in G.nodes():
    node = G.nodes[n]
    in_deg = G.in_degree(n)
    out_deg = G.out_degree(n)
    friends = node.get('friends', 0)
    followers = node.get('followers', 1)
    
    is_inorganic = (friends > 500 and (friends / max(followers, 1)) > 10) or (out_deg > 15 and in_deg < 2)
    
    node_type = 'inorganic' if is_inorganic else 'organic'
    if is_inorganic: inorganic_nodes.append(n)
    else: organic_nodes.append(n)
    
    nodes_data.append({
        "id": n,
        "group": node.get('group', 0),
        "type": node_type,
        "val": in_deg + 1,
        "tager": node.get('mentions_tager', 0),
        "aero": node.get('mentions_aero', 0),
        "label": n if n in top_hubs else ""
    })

# Identificar amplificación
bot_targets = Counter()
for b in inorganic_nodes:
    for _, target in G.out_edges(b):
        if G.nodes[target].get('type') == 'organic':
            bot_targets[target] += 1

top_bot_targets = bot_targets.most_common(10)

# Narrative Influencers
narrative_results = {}
for n_id, n_info in narratives_def.items():
    sub_nodes = [n for n in n_info['nodes'] if n in G]
    top_influencers = sorted(sub_nodes, key=lambda n: G.in_degree(n), reverse=True)[:8]
    actors_data = [{"id": a, "type": "inorganic" if a in inorganic_nodes else "organic"} for a in top_influencers]
    narrative_results[n_id] = {"title": n_info['title'], "top_actors": actors_data, "node_count": len(sub_nodes)}

# Exportar
with open('visuals/aerometro_only_text.txt', 'w') as f:
    f.write("\n---\n".join(aerometro_only_corpus))

final_json = {
    "nodes": nodes_data,
    "links": [{"source": u, "target": v, "value": int(d.get('weight', 1))} for u, v, d in G.edges(data=True)],
    "narratives": narrative_results,
    "stats": {
        "total_nodes": len(G.nodes()),
        "organic_count": len(organic_nodes),
        "inorganic_count": len(inorganic_nodes),
        "bot_percentage": round((len(inorganic_nodes)/len(G.nodes()))*100, 2) if len(G.nodes()) > 0 else 0,
        "top_bot_targets": [{"id": t, "count": c} for t, c in top_bot_targets],
        "all_bots": sorted(inorganic_nodes)[:100]
    }
}

with open('visuals/executive_network.json', 'w') as f:
    json.dump(final_json, f)

print(f"Procesamiento completo. Nodos: {len(nodes_data)}. Bots: {len(inorganic_nodes)}")
