import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

print("Generando imagen estática de alta resolución de la red...")

# Cargar el JSON exportado previamente
with open('visuals/executive_network.json', 'r') as f:
    data = json.load(f)

# Filtrar para rendimiento y limpieza visual (similar a lo que intentamos en D3)
# Quedarnos con los nodos que tienen al menos 2 conexiones o son hubs
nodes_to_keep = {n['id']: n for n in data['nodes'] if n['val'] > 1 or n['label']}
valid_node_ids = set(nodes_to_keep.keys())

# Reconstruir el grafo solo con nodos y enlaces válidos
G = nx.Graph()

for n_id, n_data in nodes_to_keep.items():
    G.add_node(n_id, **n_data)

for link in data['links']:
    # Handle D3 formatting where source/target might be dicts or strings
    u = link['source'] if isinstance(link['source'], str) else link['source'].get('id', str(link['source']))
    v = link['target'] if isinstance(link['target'], str) else link['target'].get('id', str(link['target']))
    if u in valid_node_ids and v in valid_node_ids:
        G.add_edge(u, v)

# Remover nodos aislados que hayan quedado
G.remove_nodes_from(list(nx.isolates(G)))

print(f"Renderizando {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas...")

# Layout: spring_layout (Fruchterman-Reingold force-directed algorithm)
# k ajusta la distancia óptima entre nodos (mayor = más separados)
# iterations asegura que converja
pos = nx.spring_layout(G, k=0.15, iterations=50, seed=42)

# Configurar plot (Resolución 16:9, alta calidad para PPT)
fig, ax = plt.subplots(figsize=(24, 13.5), dpi=300)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.axis('off')

# Separar listas para dibujo optimizado
organic_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'organic']
inorganic_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'inorganic']
organic_sizes = [G.nodes[n].get('val', 1) * 2 for n in organic_nodes]
inorganic_sizes = [G.nodes[n].get('val', 1) * 2 for n in inorganic_nodes]

# Dibujar aristas muy tenues
nx.draw_networkx_edges(G, pos, alpha=0.03, width=0.2, edge_color='gray', ax=ax)

# Dibujar nodos orgánicos (Azul)
nx.draw_networkx_nodes(G, pos, nodelist=organic_nodes, node_size=organic_sizes, 
                       node_color='#4285F4', alpha=0.6, ax=ax)

# Dibujar nodos inorgánicos (Rojo)
nx.draw_networkx_nodes(G, pos, nodelist=inorganic_nodes, node_size=inorganic_sizes, 
                       node_color='#e74c3c', alpha=0.8, ax=ax)

# Etiquetas (Top 20 Hubs)
labels = {n: G.nodes[n]['label'] for n in G.nodes() if G.nodes[n].get('label')}
nx.draw_networkx_labels(G, pos, labels, font_size=12, font_color='#2c3e50', 
                        font_family='sans-serif', font_weight='bold', ax=ax)

# Guardar la imagen
output_path = 'visuals/global_network_static.png'
plt.tight_layout()
plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=False)
plt.close()

print(f"Mapa estático generado exitosamente en: {output_path}")
