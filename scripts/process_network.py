import pandas as pd
import networkx as nx
from networkx.algorithms.community import label_propagation_communities
import glob
import json
import os

print("Iniciando procesamiento de la red SNA...")
G = nx.DiGraph()

# 1. Cargar Redes de Apify (Followers/Following)
redes_files = glob.glob('Dataset/Redes/*.csv')
for f in redes_files:
    try:
        df = pd.read_csv(f)
        if 'type' not in df.columns or 'target_username' not in df.columns or 'screen_name' not in df.columns:
            continue
            
        for _, row in df.iterrows():
            if pd.isna(row['target_username']) or pd.isna(row['screen_name']):
                continue
            u1 = str(row['target_username']).strip()
            u2 = str(row['screen_name']).strip()
            
            # Guardar metadatos
            if u2 not in G:
                G.add_node(u2, followers=row.get('followers_count', 0), friends=row.get('friends_count', 0))
            if u1 not in G:
                G.add_node(u1, followers=0, friends=0)
            
            if row['type'] == 'follower':
                G.add_edge(u2, u1, weight=1, type='connection')
            else:
                G.add_edge(u1, u2, weight=1, type='connection')
    except Exception as e:
        print(f"Error procesando {f}: {e}")

# 2. Cargar Interacciones (Comentarios y Quotes)
print("Procesando interacciones...")
comments_files = glob.glob('Dataset/Comments/*.csv')
quotes_files = glob.glob('Dataset/Quotes/*.csv')

for f in comments_files + quotes_files:
    try:
        df = pd.read_csv(f)
        # Check for column names
        author_col = 'author/screen_name' if 'author/screen_name' in df.columns else 'authorUsername'
        mention_cols = [c for c in df.columns if ('user_mentions' in c and 'screen_name' in c) or c == 'inReplyToUsername']
        
        if author_col in df.columns:
            for _, row in df.iterrows():
                author = row[author_col]
                if pd.isna(author): continue
                
                # Interacciones
                for mc in mention_cols:
                    mention = row[mc]
                    if not pd.isna(mention):
                        if G.has_edge(author, mention):
                            G[author][mention]['weight'] += 2
                        else:
                            G.add_edge(author, mention, weight=2, type='interaction')
    except Exception as e:
        pass

# 3. Detectar Comunidades (Clústeres narrativos)
print("Calculando comunidades y métricas...")
if G.number_of_nodes() > 0:
    G_undirected = G.to_undirected()
    communities = list(label_propagation_communities(G_undirected))

    for i, comm in enumerate(communities):
        for node in comm:
            G.nodes[node]['group'] = i

    # 4. Detectar Orgánico vs Inorgánico y Centralidad
    print("Calculando centralidad y métricas de autenticidad...")
    # Calcular degree centrality como proxy rápido de importancia
    centrality = nx.degree_centrality(G)
    top_central_nodes = sorted(centrality, key=centrality.get, reverse=True)[:20]

    for node in G.nodes():
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        
        friends = G.nodes[node].get('friends', 0)
        followers = G.nodes[node].get('followers', 1) 
        
        is_inorganic = False
        if pd.notna(friends) and pd.notna(followers):
            if float(friends) > 500 and (float(friends) / max(float(followers), 1)) > 10:
                is_inorganic = True
                
        if out_deg > 15 and in_deg < 2:
            is_inorganic = True

        G.nodes[node]['type'] = 'inorganic' if is_inorganic else 'organic'
        G.nodes[node]['val'] = in_deg + 1
        # Marcar para etiqueta si es central o es bot activo
        G.nodes[node]['show_label'] = True if (node in top_central_nodes or (is_inorganic and out_deg > 10)) else False

# 5. Exportar a JSON para D3.js
data = {
    "nodes": [
        {
            "id": str(n), 
            "group": G.nodes[n].get('group', 0), 
            "type": G.nodes[n].get('type', 'organic'), 
            "val": G.nodes[n].get('val', 1),
            "label": str(n) if G.nodes[n].get('show_label') else ""
        } for n in G.nodes()
    ],
    "links": [{"source": str(u), "target": str(v), "value": int(d.get('weight', 1))} for u, v, d in G.edges(data=True)]
}

os.makedirs('visuals', exist_ok=True)
with open('visuals/network_data.json', 'w') as f:
    json.dump(data, f)

print(f"Red generada con éxito: {G.number_of_nodes()} nodos, {G.number_of_edges()} relaciones.")
