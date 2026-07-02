"""Genera nubes de palabras por narrativa para el sitio de scrollytelling,
con un color fijo por narrativa, más una nube aparte para "Medios" (todo el
texto de reacciones a tuits de medios, sin filtrar por palabra clave).
"""
import glob
import os
from collections import Counter

import pandas as pd
import spacy
from wordcloud import WordCloud

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "scrollytelling-site", "visuals")

nlp = spacy.load("es_core_news_sm")


def load_stopwords(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            words = [w.strip().lower() for w in f.read().split(",")]
        return set(words)
    except Exception:
        return set()


stopwords = load_stopwords(os.path.join(BASE, "scripts", "stopWords.txt"))
stopwords.update({"que", "por", "con", "para", "como", "esto", "esta", "este", "pero", "más",
                   "sus", "una", "uno", "es", "ser"})


def clean_text_spacy(text):
    if not isinstance(text, str):
        return []
    import re
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[@#]\S+", "", text)
    doc = nlp(text.lower())
    return [t.lemma_ for t in doc if t.is_alpha and t.lemma_ not in stopwords and len(t.lemma_) > 2]


# Narrativas por palabra clave (mismas que scripts/export_executive_json.py),
# con un color fijo cada una (paleta categórica validada por accesibilidad).
NARRATIVES = {
    "Decepcion_Traicion_Politica": {
        "title": "Decepción y traición política",
        "keywords": ["arévalo", "arevalo", "bernardo", "bernie", "semilla", "tibio", "tibios",
                     "traidor", "traición", "decepción", "cobarde", "usurpador", "legitimidad", "exilio"],
        "color": "#4a3aa7",
        "words": [],
    },
    "USAC_Fraude_Rectoria": {
        "title": "USAC: fraude y crisis de rectoría",
        "keywords": ["usac", "universidad", "estudiantes", "mazariegos", "rector", "fraude",
                     "elecciones", "consejo superior", "csu"],
        "color": "#e34948",
        "words": [],
    },
    "Pactos_y_Corrupcion": {
        "title": "Pactos y corrupción opaca",
        "keywords": ["corrup", "pacto", "cacif", "mordida", "cómplice", "negocio turbio"],
        "color": "#eb6834",
        "words": [],
    },
    "Ana_Glenda_Tager": {
        "title": "Figura de Ana Glenda Tager",
        "keywords": ["tager", "glenda"],
        "color": "#e87ba4",
        "words": [],
    },
    "Plan_Infraestructura_Quinonez": {
        "title": "Plan de infraestructura / Ricardo Quiñonez",
        "keywords": ["quiñon", "quinon", "infraestructura", "aeropuerto", "carretera", "obra",
                     "contrato", "licitac", "presupuesto"],
        "color": "#1baf7a",
        "words": [],
    },
}
MEDIOS_COLOR = "#eda100"
medios_words = []


def color_fn(hex_color):
    return lambda *args, **kwargs: hex_color


def load_files(pattern):
    for f in glob.glob(pattern, recursive=True):
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        text_col = "text" if "text" in df.columns else "display_text"
        if text_col not in df.columns:
            continue
        yield f, df[text_col].dropna().tolist()


for f, texts in load_files(os.path.join(BASE, "Dataset", "Comments", "**", "*.csv")):
    is_medios = os.sep + "Medios" + os.sep in f
    for text in texts:
        lower_text = text.lower()
        if is_medios:
            medios_words.extend(clean_text_spacy(text))
        for key, info in NARRATIVES.items():
            if any(kw in lower_text for kw in info["keywords"]):
                info["words"].extend(clean_text_spacy(text))

for f, texts in load_files(os.path.join(BASE, "Dataset", "Quotes", "**", "*.csv")):
    is_medios = os.sep + "Medios" + os.sep in f
    for text in texts:
        lower_text = text.lower()
        if is_medios:
            medios_words.extend(clean_text_spacy(text))
        for key, info in NARRATIVES.items():
            if any(kw in lower_text for kw in info["keywords"]):
                info["words"].extend(clean_text_spacy(text))

os.makedirs(OUT_DIR, exist_ok=True)

for key, info in NARRATIVES.items():
    if info["words"]:
        freq = Counter(info["words"])
        WordCloud(width=800, height=400, background_color="white",
                  color_func=color_fn(info["color"]), max_words=50) \
            .generate_from_frequencies(freq).to_file(os.path.join(OUT_DIR, f"wc_{key}.png"))
        print(f"Nube '{info['title']}' generada ({len(freq)} palabras únicas).")
    else:
        print(f"Sin datos suficientes para narrativa '{key}'.")

if medios_words:
    freq = Counter(medios_words)
    WordCloud(width=800, height=400, background_color="white",
              color_func=color_fn(MEDIOS_COLOR), max_words=50) \
        .generate_from_frequencies(freq).to_file(os.path.join(OUT_DIR, "wc_Medios.png"))
    print(f"Nube 'Medios' generada ({len(freq)} palabras únicas).")
else:
    print("Sin datos suficientes para la nube de Medios.")

print("Nubes de palabras generadas en", OUT_DIR)
