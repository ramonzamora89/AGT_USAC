
import json
from bs4 import BeautifulSoup

def pre_render_html_final(template_path, json_path, output_path):
    """
    Loads a template HTML, injects dynamic content from a JSON file using robust
    BeautifulSoup methods, and saves a complete, static HTML file.
    """
    print("--- INICIANDO PRE-RENDERIZADO DEL HTML (VERSIÓN FINAL) ---")

    with open(template_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Generate and inject narrative slides
    narrative_placeholder = soup.find(id='narrative-slides')
    if narrative_placeholder:
        narratives = data.get('narratives', {})
        print(f"Encontradas {len(narratives)} narrativas para generar.")
        
        for key, info in narratives.items():
            slide = soup.new_tag('div', **{'class': 'slide'})
            
            # Title
            title = soup.new_tag('h1')
            title.string = info.get('title', 'Sin Título')
            slide.append(title)
            
            grid = soup.new_tag('div', **{'class': 'grid'})
            
            # Left Column
            left_card = soup.new_tag('div', **{'class': 'card'})
            h2_left = soup.new_tag('h2'); h2_left.string = "Análisis del clúster"
            p_actors = soup.new_tag('p'); p_actors.string = f"Actores: {info.get('node_count', 0):,}"
            h3_influencers = soup.new_tag('h3'); h3_influencers.string = "Influencers clave:"
            ul_actors = soup.new_tag('ul', **{'class': 'actor-list', 'style': 'grid-template-columns: 1fr;'})
            for a in info.get('top_actors', []):
                li = soup.new_tag('li', **{'class': f'actor-{a.get("type", "organic")}'})
                li.string = f'@{a.get("id", "N/A")} '
                span_type = soup.new_tag('span', style="float:right;")
                span_type.string = f'[{a.get("type", "organic")}]'
                li.append(span_type)
                ul_actors.append(li)
            left_card.extend([h2_left, p_actors, h3_influencers, ul_actors])
            
            # Right Column
            right_card = soup.new_tag('div', **{'class': 'card'})
            h2_right = soup.new_tag('h2'); h2_right.string = "Nube de palabras"
            img_wc = soup.new_tag('img', src=f"../visuals/wc_{key}.png", **{'class': 'wc-img'})
            right_card.extend([h2_right, img_wc])

            grid.extend([left_card, right_card])
            slide.append(grid)
            
            narrative_placeholder.insert_before(slide)

        narrative_placeholder.decompose()

    # 2. Populate bot list
    bot_list_placeholder = soup.find(id='bot-list')
    if bot_list_placeholder:
        all_bots = data.get('stats', {}).get('all_bots', [])
        bot_list_placeholder.clear() # Remove any existing content
        for bot in all_bots[:21]:
            li = soup.new_tag('li', **{'class': 'actor-inorganic'})
            li.string = f"@{bot}"
            bot_list_placeholder.append(li)

    # 3. Remove the script tag
    script_tag = soup.find('script', src=None)
    if script_tag:
        script_tag.decompose()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
    print(f"HTML estático final generado con éxito en: {output_path}")

if __name__ == '__main__':
    pre_render_html_final(
        'reports/reporte_ejecutivo_final.html',
        'visuals/executive_network.json',
        'reports/reporte_final_estatico.html'
    )
