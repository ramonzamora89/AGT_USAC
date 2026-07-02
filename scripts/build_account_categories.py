"""Genera una tabla de referencia (screen_name -> categoria) para poder
etiquetar el dataset de redes (follower/following), que llega como una
sola tabla mezclando cuentas de medios y de usuarios comunes.

Clasificación confiable disponible hoy: solo los autores de los tuits
originales (resueltos en extract_unique_users.resolve_original_authors),
ya que esa categoría viene de la carpeta Medios/Usuarios donde tú
clasificaste el tuit semilla. El resto de cuentas (comentantes/citadores,
y cualquier target_username del dataset de redes que no sea autor
original) queda como "pendiente" hasta que se procese el dataset de
perfiles con el actor de extracción de perfiles.
"""
from pathlib import Path

import pandas as pd

from extract_unique_users import DATASET, resolve_original_authors

REDES_DATASET = DATASET / "dataset_premium-x-follower-scraper-following-data_2026-07-02_19-16-57-344.csv"

# Confirmado directamente por el usuario (metodología: 29 tuits semilla de Brand24,
# cuentas con publicaciones de >20k de alcance; estas son las que son medios de
# comunicación, el resto de las 29 son usuarios comunes).
#
# Nota: Noti7Guatemala fue identificado por Brand24 con alcance, pero su tuit
# semilla no tuvo comentarios ni quote RTs (sin impacto real), así que no se
# incluyó en la extracción y queda fuera de este análisis.
MEDIOS_CONFIRMADOS = {
    "lahoragt",
    "soy_502",
    "ep_investiga",
    "diariodeca",
    "nuestrodiario",
    "canalantigua",
    "publinewsgt",
}


def main():
    # 1. Clasificación confiable: autores originales (Medios/Usuarios por carpeta semilla)
    original_frames = resolve_original_authors()
    known = {}  # screen_name_lower -> (screen_name, categoria, fuente_clasificacion)
    conflicts = {}
    if original_frames:
        df = pd.concat(original_frames, ignore_index=True)
        for sn, group in df.groupby(df["screen_name"].str.lower()):
            cats = set(group["origen_categoria"])
            if len(cats) > 1:
                conflicts[sn] = cats
                continue
            known[sn] = (group["screen_name"].iloc[0], cats.pop(), "autor_original_confirmado")

    if conflicts:
        print(f"[aviso] {len(conflicts)} cuentas fueron autor_original de tuits en ambas categorías, se dejan pendientes: {conflicts}")

    # 2. La lista de medios confirmada directamente por el usuario tiene prioridad sobre la inferencia
    for sn_lower in MEDIOS_CONFIRMADOS:
        prev = known.get(sn_lower)
        if prev and prev[1] != "Medios":
            print(f"[aviso] {prev[0]} se había inferido como '{prev[1]}' pero el usuario lo confirmó como Medios; se corrige")
        display_name = prev[0] if prev else sn_lower
        known[sn_lower] = (display_name, "Medios", "confirmado_usuario")

    # 3. Universo completo de cuentas a etiquetar: el listado que se usó para pedir el dataset de redes
    users_txt = DATASET / "apify_users_list.txt"
    universo = [u.strip() for u in users_txt.read_text(encoding="utf-8").splitlines() if u.strip()]

    # target_username realmente presentes en el dataset de redes ya descargado (por si difieren)
    if REDES_DATASET.exists():
        redes_df = pd.read_csv(REDES_DATASET, encoding="utf-8-sig", dtype=str, usecols=["target_username"])
        presentes_en_redes = set(redes_df["target_username"].dropna().str.lower())
        faltantes = presentes_en_redes - {u.lower() for u in universo}
        if faltantes:
            print(f"[aviso] {len(faltantes)} target_username en el dataset de redes no están en apify_users_list.txt: {faltantes}")
    else:
        print(f"[aviso] no se encontró {REDES_DATASET.name}, se usa solo apify_users_list.txt como universo")

    universo_keys = {u.lower() for u in universo}
    rows = []
    for u in universo:
        key = u.lower()
        if key in known:
            screen_name, categoria, fuente = known[key]
            rows.append({"screen_name": screen_name, "categoria": categoria, "fuente_clasificacion": fuente})
        else:
            rows.append({"screen_name": u, "categoria": "pendiente", "fuente_clasificacion": "pendiente_perfil"})

    # Medios confirmados por el usuario que no aparecen en el universo (ni en apify_users_list.txt
    # ni en el dataset de redes) igual se agregan, marcados, para no perder el dato.
    for sn_lower in MEDIOS_CONFIRMADOS:
        if sn_lower not in universo_keys:
            screen_name, categoria, _ = known[sn_lower]
            rows.append({"screen_name": screen_name, "categoria": categoria, "fuente_clasificacion": "confirmado_usuario_fuera_de_dataset"})
            print(f"[aviso] {screen_name} confirmado como Medios pero no está en apify_users_list.txt ni en el dataset de redes")

    out = pd.DataFrame(rows).sort_values(["categoria", "screen_name"])
    out_path = DATASET / "account_categories.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\nTotal cuentas: {len(out)}")
    print(out["categoria"].value_counts().to_string())
    print(f"\nReferencia guardada en: {out_path}")


if __name__ == "__main__":
    main()
