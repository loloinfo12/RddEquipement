import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from contextlib import contextmanager
import requests
import re

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Rêve de Dragon – Équipement",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  STYLE
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;800&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

:root {
    --parchment: #f5ead0;
    --ink:        #2c1a0e;
    --blood:      #8b1a1a;
    --gold:       #b8860b;
    --shadow:     #5c3a1e;
    --bg:         #1a0f05;
}

html, body, [class*="css"] {
    font-family: 'Crimson Text', Georgia, serif;
    background-color: var(--bg) !important;
    color: var(--parchment) !important;
}
h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: var(--gold) !important;
    letter-spacing: 0.05em;
}
.stButton > button {
    background: var(--blood) !important;
    color: var(--parchment) !important;
    border: 1px solid var(--gold) !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    border-radius: 2px !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: var(--gold) !important;
    color: var(--ink) !important;
}
.stDataFrame, .stTable {
    background: rgba(245, 234, 208, 0.05) !important;
    border: 1px solid var(--gold) !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput input,
.stTextArea textarea {
    background: rgba(245, 234, 208, 0.08) !important;
    color: var(--parchment) !important;
    border: 1px solid var(--shadow) !important;
    font-family: 'Crimson Text', serif !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea textarea::placeholder {
    color: rgba(245, 234, 208, 0.35) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
    color: var(--parchment) !important;
    background: rgba(245, 234, 208, 0.12) !important;
    border-color: var(--gold) !important;
}
input[type="text"],
input[type="password"],
input[type="number"],
input[type="email"],
input {
    color: #f5ead0 !important;
    -webkit-text-fill-color: #f5ead0 !important;
    caret-color: #f5ead0 !important;
}
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
    -webkit-text-fill-color: #f5ead0 !important;
    box-shadow: 0 0 0px 1000px #1a0f05 inset !important;
}
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextInput"] input:active,
[data-testid="stTextInput"] input:hover,
div[class*="st-"] input {
    color: #f5ead0 !important;
    -webkit-text-fill-color: #f5ead0 !important;
    background-color: rgba(245, 234, 208, 0.08) !important;
}
[data-baseweb="input"] input::placeholder,
[data-testid="stTextInput"] input::placeholder {
    color: rgba(245, 234, 208, 0.3) !important;
    -webkit-text-fill-color: rgba(245, 234, 208, 0.3) !important;
}
.stSidebar {
    background: rgba(10, 5, 2, 0.95) !important;
    border-right: 1px solid var(--gold) !important;
}
.metric-card {
    background: rgba(184, 134, 11, 0.1);
    border: 1px solid var(--gold);
    border-radius: 4px;
    padding: 1rem;
    text-align: center;
}
.metric-value {
    font-family: 'Cinzel', serif;
    font-size: 2rem;
    color: var(--gold);
}
.metric-label {
    font-size: 0.85rem;
    color: rgba(245,234,208,0.6);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.banner {
    text-align: center;
    padding: 2rem 0 1rem;
    border-bottom: 1px solid var(--gold);
    margin-bottom: 2rem;
}
.banner h1 { font-size: 2.8rem !important; text-shadow: 0 0 20px rgba(184,134,11,0.4); }
.banner p  { color: rgba(245,234,208,0.5); font-style: italic; font-size: 1.1rem; }
div[data-testid="stAlert"] {
    background: rgba(139,26,26,0.2) !important;
    border: 1px solid var(--blood) !important;
    color: var(--parchment) !important;
}
.tag {
    display: inline-block;
    background: rgba(184,134,11,0.15);
    border: 1px solid var(--gold);
    color: var(--gold);
    padding: 2px 10px;
    border-radius: 2px;
    font-size: 0.75rem;
    font-family: 'Cinzel', serif;
    letter-spacing: 0.05em;
    margin: 2px;
}
hr { border-color: var(--gold) !important; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  COLONNES ARMES
# ─────────────────────────────────────────────
COLS_ARMES_COMMUNES = ["degats", "mains", "force_requise", "resistance"]
COLS_ARMES_TIR      = ["m_distance", "portee_max", "magasin", "tir_rechargement"]

SOUS_CAT_TIR = {"Arbalètes", "Arcs", "Armes de poing", "Armes d'épaule"}

LABELS_COMMUNES = {
    "degats":        "Dégâts",
    "mains":         "Mains",
    "force_requise": "Force requise",
    "resistance":    "Résistance",
}
LABELS_TIR = {
    "m_distance":       "M. distance",
    "portee_max":       "Portée max",
    "magasin":          "Magasin",
    "tir_rechargement": "Tir/Rechargement",
}

def is_tir(sous_categorie: str) -> bool:
    return str(sous_categorie) in SOUS_CAT_TIR

# ─────────────────────────────────────────────
#  CONNEXION NEON
# ─────────────────────────────────────────────
@contextmanager
def get_conn():
    conn = psycopg2.connect(
        st.secrets["DATABASE_URL"],
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def query(sql: str, params=None) -> list:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def execute(sql: str, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())

def executemany(sql: str, data: list):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, data)

# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def login(username: str, password: str):
    rows = query(
        "SELECT * FROM users WHERE username=%s AND password_hash=%s",
        (username, hash_password(password))
    )
    return dict(rows[0]) if rows else None

# ─────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_equipements() -> pd.DataFrame:
    rows = query("""SELECT id, categorie, sous_categorie, nom, poids_kg, prix_deniers, notes, degats, mains, force_requise, resistance, m_distance, portee_max, magasin, tir_rechargement, svg_illustration FROM equipements ORDER BY categorie, sous_categorie, nom""")
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

@st.cache_data(ttl=30)
def load_inventory(player_id: int) -> pd.DataFrame:
    rows = query("""
        SELECT i.id AS inv_id, i.quantite, i.localisation,
               e.id AS eq_id, e.nom, e.categorie, e.sous_categorie,
               e.poids_kg, e.prix_deniers, e.notes,
               e.degats, e.mains, e.force_requise, e.resistance,
               e.m_distance, e.portee_max, e.magasin, e.tir_rechargement
        FROM inventaire i
        JOIN equipements e ON e.id = i.equipement_id
        WHERE i.player_id = %s
        ORDER BY i.localisation, e.categorie, e.nom
    """, (player_id,))
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

@st.cache_data(ttl=30)
def load_player_info(player_id: int) -> dict:
    rows = query("SELECT id, username, monture, poids_max_joueur FROM users WHERE id=%s", (player_id,))
    return dict(rows[0]) if rows else {}

@st.cache_data(ttl=30)
def load_players() -> list:
    rows = query("SELECT id, username, role FROM users WHERE role='joueur' ORDER BY username")
    return [dict(r) for r in rows]

def invalidate_cache():
    load_equipements.clear()
    load_inventory.clear()
    load_players.clear()
    load_player_info.clear()

MONTURES = ["Aucune", "Cheval", "Mule / Âne", "Charrette", "Aligate", "Autre"]

# ─────────────────────────────────────────────
#  UPLOAD MANUEL D'ILLUSTRATION
# ─────────────────────────────────────────────
def image_vers_base64(uploaded_file) -> str | None:
    try:
        import base64
        data = uploaded_file.read()
        mime = uploaded_file.type or "image/jpeg"
        b64  = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def telecharger_url_base64(url: str) -> str | None:
    try:
        import base64
        resp = requests.get(
            url, timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RDD-App/1.0)"},
            allow_redirects=True
        )
        if resp.status_code != 200:
            return None
        mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        if not mime.startswith("image/"):
            mime = "image/jpeg"
        b64 = base64.b64encode(resp.content).decode()
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def generer_svg_arme(nom: str, sous_categorie: str, notes: str, degats: str = "") -> str | None:
    prompt = f"""Tu es un illustrateur médiéval spécialisé dans les armes fantasy.
Crée un SVG 300×400 illustrant cette arme de manière artistique, dans un style gravure médiévale sur parchemin clair.

Arme : {nom}
Catégorie : {sous_categorie}
Description : {notes}
Dégâts : {degats or "non précisé"}

Règles ABSOLUES — respecte-les toutes sans exception :
- SVG viewBox="0 0 300 400" xmlns="http://www.w3.org/2000/svg"
- FOND OBLIGATOIRE : commence par <rect width="300" height="400" fill="#f5ead0"/> (parchemin clair)
- Toutes les lignes, contours et détails : stroke="#2c1a0e" (brun très foncé), fill="none" ou fill="#2c1a0e"
- JAMAIS de couleurs sombres comme #000, #111, #1a0f05 ou similaires pour le fond
- Style gravure : traits fins (stroke-width entre 0.8 et 2), hachures, détails minutieux
- L'arme DOIT occuper AU MINIMUM 80% de la surface totale du SVG (300×400)
- Centre le dessin exactement sur x=150, y=180 (centre du SVG hors texte)
- L'arme doit être GRANDE : utilise tout l'espace de x=20 à x=280 et y=20 à y=340
- Incline légèrement l'arme (rotate entre 10° et 30°) pour un effet dynamique
- Ajoute des hachures fines pour les ombres et du volume
- Petits détails décoratifs (runes, ornements, gravures) sur la lame ou le manche
- En bas (y=375) : nom en petites capitales centré, font-family="serif", fill="#b8860b", font-size="13", text-anchor="middle", x="150"
- PAS de texte descriptif superflu
- Renvoie UNIQUEMENT le code SVG brut, sans markdown, sans explication, sans balise ```"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": st.secrets["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        match = re.search(r'(<svg[\s\S]*?</svg>)', text, re.IGNORECASE)
        return match.group(1) if match else text.strip()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None


def _afficher_image_stockee(data_uri: str, nom: str):
    if data_uri.startswith("data:image/"):
        st.markdown(f"""
        <div style="border:2px solid #b8860b;border-radius:6px;padding:8px;
                    background:#1a0f05;display:flex;justify-content:center;">
            <img src="{data_uri}" style="max-width:100%;max-height:380px;
                       object-fit:contain;border-radius:4px;" alt="{nom}"/>
        </div>""", unsafe_allow_html=True)
    elif data_uri.strip().startswith("<svg"):
        svg_clean = re.sub(
            r'<rect[^>]*fill="#(?:1a0f05|0d0a07|111|000000|1f1f1f|0a0500)[^"]*"[^>]*/?>'
,
            '', data_uri, flags=re.IGNORECASE
        )
        st.markdown(f"""
        <div style="border:2px solid #b8860b;border-radius:6px;padding:12px;
                    background:#f5ead0;display:flex;justify-content:center;
                    max-width:320px;margin:0 auto;">{svg_clean}</div>
        """, unsafe_allow_html=True)


def afficher_illustration(row: pd.Series, is_admin: bool = False, key_prefix: str = ""):
    nom     = str(row.get("nom", ""))
    stockee = row.get("svg_illustration", "") or ""
    sous_cat= str(row.get("sous_categorie", ""))
    notes   = str(row.get("notes", "") or "")
    degats  = str(row.get("degats", "") or "")
    eq_id   = row.get("id", None)

    has_img = bool(stockee and (stockee.startswith("data:image/") or stockee.strip().startswith("<svg")))
    icon    = "🖼️" if has_img else "✦"

    with st.expander(f"{icon} {nom}"):
        if has_img:
            _afficher_image_stockee(stockee, nom)
            if is_admin and eq_id is not None:
                if st.button("🗑️ Supprimer l'illustration", key=f"del_img_{key_prefix}_{eq_id}"):
                    execute("UPDATE equipements SET svg_illustration=NULL WHERE id=%s", (int(eq_id),))
                    invalidate_cache()
                    st.success("Illustration supprimée.")
                    st.rerun()
        else:
            st.caption("Aucune illustration pour cette arme.")

        if is_admin and eq_id is not None:
            st.markdown("---")

            method = st.radio(
                "Ajouter une illustration",
                ["🔗 Coller une URL", "📂 Upload fichier"],
                horizontal=True,
                key=f"method_{key_prefix}_{eq_id}"
            )

            if method == "🔗 Coller une URL":
                st.caption("Clic droit sur n'importe quelle image dans votre navigateur → **Copier l'adresse de l'image** → coller ici")
                url_input = st.text_input(
                    "URL de l'image",
                    placeholder="https://...",
                    key=f"url_{key_prefix}_{eq_id}"
                )
                if url_input and url_input.startswith("http"):
                    try:
                        st.image(url_input, caption="Aperçu", width=250)
                        if st.button("✅ Valider cette image", key=f"save_url_{key_prefix}_{eq_id}"):
                            with st.spinner("Téléchargement..."):
                                b64 = telecharger_url_base64(url_input)
                            if b64:
                                execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s",
                                        (b64, int(eq_id)))
                                invalidate_cache()
                                st.success(f"Illustration de « {nom} » sauvegardée !")
                                st.rerun()
                            else:
                                st.error("Impossible de télécharger cette image. Essayez de la sauvegarder puis d'uploader le fichier.")
                    except Exception:
                        st.warning("URL invalide ou image inaccessible.")

            else:
                uploaded = st.file_uploader(
                    "Glissez-déposez ou choisissez un fichier",
                    type=["png", "jpg", "jpeg", "webp", "gif", "svg"],
                    key=f"upload_{key_prefix}_{eq_id}",
                )
                if uploaded is not None:
                    st.image(uploaded, caption="Aperçu", width=250)
                    if st.button("✅ Valider cette image", key=f"save_img_{key_prefix}_{eq_id}"):
                        if uploaded.type == "image/svg+xml":
                            svg_text = uploaded.read().decode("utf-8", errors="ignore")
                            execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s",
                                    (svg_text, int(eq_id)))
                        else:
                            b64 = image_vers_base64(uploaded)
                            if b64:
                                execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s",
                                        (b64, int(eq_id)))
                        invalidate_cache()
                        st.success(f"Illustration de « {nom} » sauvegardée !")
                        st.rerun()

            st.markdown("")
            with st.expander("🎨 Générer un SVG avec Claude"):
                btn_lbl = "Regénérer le SVG" if has_img and stockee.strip().startswith("<svg") else "Générer un SVG"
                if st.button(btn_lbl, key=f"gen_svg_{key_prefix}_{eq_id}"):
                    with st.spinner(f"Génération SVG de « {nom} »..."):
                        nouveau_svg = generer_svg_arme(nom, sous_cat, notes, degats)
                    if nouveau_svg:
                        execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s",
                                (nouveau_svg, int(eq_id)))
                        invalidate_cache()
                        st.success("SVG sauvegardé !")
                        st.rerun()
                    else:
                        st.error("La génération a échoué.")

# ─────────────────────────────────────────────
#  HELPERS D'AFFICHAGE DU CATALOGUE
# ─────────────────────────────────────────────
def _cols_display_melee(df: pd.DataFrame) -> tuple[list, dict]:
    base  = ["categorie","sous_categorie","nom","poids_kg","prix_deniers"]
    stats = [c for c in COLS_ARMES_COMMUNES if c in df.columns]
    extra = ["notes"]
    cols  = [c for c in base + stats + extra if c in df.columns]
    rename = {
        "categorie":"Catégorie","sous_categorie":"Sous-catégorie",
        "nom":"Nom","poids_kg":"Poids (kg)","prix_deniers":"Prix (deniers)","notes":"Notes",
        **{k: v for k, v in LABELS_COMMUNES.items()},
    }
    return cols, rename

def _cols_display_tir(df: pd.DataFrame) -> tuple[list, dict]:
    base  = ["categorie","sous_categorie","nom","poids_kg","prix_deniers"]
    stats = [c for c in COLS_ARMES_COMMUNES[:1] + COLS_ARMES_TIR if c in df.columns]
    extra = ["notes"]
    cols  = [c for c in base + stats + extra if c in df.columns]
    rename = {
        "categorie":"Catégorie","sous_categorie":"Sous-catégorie",
        "nom":"Nom","poids_kg":"Poids (kg)","prix_deniers":"Prix (deniers)","notes":"Notes",
        **{k: v for k, v in LABELS_COMMUNES.items()},
        **{k: v for k, v in LABELS_TIR.items()},
    }
    return cols, rename

def afficher_catalogue(df: pd.DataFrame, key_prefix: str = "cat", is_admin: bool = False):
    if df.empty:
        st.info("Le catalogue est vide.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        cats = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
        cat_filter = st.selectbox("Catégorie", cats, key=f"{key_prefix}_cat")
    with c2:
        sub_df = df[df["categorie"] == cat_filter] if cat_filter != "Toutes" else df
        sous = ["Toutes"] + sorted(sub_df["sous_categorie"].dropna().unique().tolist())
        sous_filter = st.selectbox("Sous-catégorie", sous, key=f"{key_prefix}_sous")
    with c3:
        search = st.text_input("🔍 Rechercher", placeholder="Nom de l'objet...", key=f"{key_prefix}_search")

    filtered = df.copy()
    if cat_filter  != "Toutes": filtered = filtered[filtered["categorie"]      == cat_filter]
    if sous_filter != "Toutes": filtered = filtered[filtered["sous_categorie"] == sous_filter]
    if search:                  filtered = filtered[filtered["nom"].str.contains(search, case=False, na=False)]

    st.markdown(f"**{len(filtered)}** objet(s) trouvé(s)")

    mask_tir = filtered["sous_categorie"].apply(is_tir) if "sous_categorie" in filtered.columns else pd.Series(False, index=filtered.index)
    df_melee = filtered[~mask_tir]
    df_tir   = filtered[mask_tir]

    tab_melee, tab_tir = st.tabs([f"⚔️ Armes de mêlée ({len(df_melee)})", f"🏹 Armes de tir ({len(df_tir)})"])

    def _render_section(df_section, cols_fn, tab_prefix):
        if df_section.empty:
            st.caption("Aucune arme dans cette sélection.")
            return
        cols, rename = cols_fn(df_section)
        st.dataframe(df_section[cols].rename(columns=rename), use_container_width=True, hide_index=True)
        st.markdown("#### 🖼️ Illustrations")
        rows_list = [df_section.iloc[i] for i in range(len(df_section))]
        for i in range(0, len(rows_list), 3):
            grid_cols = st.columns(3)
            for j, col in enumerate(grid_cols):
                if i + j < len(rows_list):
                    with col:
                        afficher_illustration(
                            rows_list[i + j],
                            is_admin=is_admin,
                            key_prefix=f"{tab_prefix}_{i+j}"
                        )

    with tab_melee:
        _render_section(df_melee, _cols_display_melee, f"{key_prefix}_mel")

    with tab_tir:
        _render_section(df_tir, _cols_display_tir, f"{key_prefix}_tir")

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─────────────────────────────────────────────
#  PAGE : LOGIN
# ─────────────────────────────────────────────
def page_login():
    st.markdown("""
    <div class="banner">
        <h1>🐉 Rêve de Dragon</h1>
        <p>Gestion de l'équipement des aventuriers</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### Identification")
        username = st.text_input("Nom d'aventurier", placeholder="Votre identifiant...")
        password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
        if st.button("🗝️  Entrer dans la taverne", use_container_width=True):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Identifiants incorrects. Le portier vous refuse l'entrée.")

# ─────────────────────────────────────────────
#  PAGE : ADMIN
# ─────────────────────────────────────────────
def page_admin():
    user = st.session_state.user
    st.markdown(f"""
    <div class="banner">
        <h1>🐉 Rêve de Dragon</h1>
        <p>Tableau du Maître des Rêves — {user['username']}</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["⚔️ Catalogue", "➕ Ajouter équipement", "🎒 Inventaires joueurs", "👤 Gestion joueurs"])

    # ── TAB 1 : Catalogue ──
    with tab1:
        df = load_equipements()
        afficher_catalogue(df, key_prefix="admin_cat", is_admin=True)

        st.markdown("---")
        st.markdown("##### ✏️ Modifier les stats d'une arme")
        if not df.empty:
            to_edit = st.selectbox("Sélectionner l'arme à modifier", sorted(df["nom"].tolist()), key="admin_edit_sel")
            row_edit = df[df["nom"] == to_edit].iloc[0]
            eq_id_edit = int(row_edit["id"])

            sous_cat_edit = str(row_edit.get("sous_categorie", ""))
            tir_mode = is_tir(sous_cat_edit)

            with st.form(key="form_edit_arme"):
                st.markdown(f"**{to_edit}** — *{sous_cat_edit}*")

                # ── Champ Notes en pleine largeur ──
                edit_notes = st.text_input("Notes", value=str(row_edit.get("notes") or ""))

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    edit_degats = st.text_input("Dégâts", value=str(row_edit.get("degats") or ""))
                    edit_mains  = st.text_input("Mains",  value=str(row_edit.get("mains")  or ""))
                with c2:
                    edit_force = st.text_input("Force requise", value=str(row_edit.get("force_requise") or ""))
                    edit_res   = st.text_input("Résistance",    value=str(row_edit.get("resistance")    or ""))
                with c3:
                    if tir_mode:
                        edit_m_dist = st.text_input("M. distance", value=str(row_edit.get("m_distance") or ""))
                        edit_portee = st.text_input("Portée max",  value=str(row_edit.get("portee_max") or ""))
                    else:
                        edit_m_dist = edit_portee = ""
                with c4:
                    if tir_mode:
                        edit_magasin = st.text_input("Magasin",            value=str(row_edit.get("magasin")          or ""))
                        edit_tir_rech= st.text_input("Tir/Rechargement",   value=str(row_edit.get("tir_rechargement") or ""))
                    else:
                        edit_magasin = edit_tir_rech = ""

                if st.form_submit_button("💾 Sauvegarder les stats"):
                    if tir_mode:
                        execute("""
                            UPDATE equipements
                            SET notes=%s, degats=%s, mains=%s, force_requise=%s, resistance=%s,
                                m_distance=%s, portee_max=%s, magasin=%s, tir_rechargement=%s
                            WHERE id=%s
                        """, (
                            edit_notes or None,
                            edit_degats or None, edit_mains or None,
                            edit_force  or None, edit_res   or None,
                            edit_m_dist or None, edit_portee or None,
                            edit_magasin or None, edit_tir_rech or None,
                            eq_id_edit
                        ))
                    else:
                        execute("""
                            UPDATE equipements
                            SET notes=%s, degats=%s, mains=%s, force_requise=%s, resistance=%s
                            WHERE id=%s
                        """, (
                            edit_notes or None,
                            edit_degats or None, edit_mains or None,
                            edit_force  or None, edit_res   or None,
                            eq_id_edit
                        ))
                    invalidate_cache()
                    st.success(f"Stats de « {to_edit} » mises à jour.")
                    st.rerun()

        st.markdown("---")
        st.markdown("##### 🗑️ Supprimer un équipement")
        if not df.empty:
            to_delete = st.selectbox("Sélectionner l'objet à supprimer", sorted(df["nom"].tolist()), key="admin_del")
            if st.button("Supprimer cet objet", type="primary"):
                obj_id = int(df[df["nom"] == to_delete]["id"].values[0])
                execute("DELETE FROM equipements WHERE id=%s", (obj_id,))
                invalidate_cache()
                st.success(f"« {to_delete} » retiré du catalogue.")
                st.rerun()

    # ── TAB 2 : Ajouter équipement ──
    with tab2:
        st.markdown("#### Ajouter manuellement")
        c1, c2 = st.columns(2)
        with c1:
            new_cat   = st.text_input("Catégorie", value="Armes")
            new_sous  = st.text_input("Sous-catégorie")
            new_nom   = st.text_input("Nom de l'objet")
            new_notes = st.text_input("Notes (optionnel)")
        with c2:
            new_poids = st.number_input("Poids (kg)",       min_value=0.0, step=0.05, format="%.2f")
            new_prix  = st.number_input("Prix (deniers)",   min_value=0,   step=10)
            new_degats= st.text_input("Dégâts (+dom)",      placeholder="ex: A+3")
            new_mains = st.text_input("Mains",              placeholder="ex: 1 ou 1\\2")
            new_force = st.text_input("Force requise",      placeholder="ex: 11")
            new_res   = st.text_input("Résistance",         placeholder="ex: 12")

        tir_mode_new = is_tir(new_sous)
        if tir_mode_new:
            st.markdown("**Spécifique armes de tir**")
            c1t, c2t, c3t, c4t = st.columns(4)
            with c1t: new_m_dist  = st.text_input("M. distance")
            with c2t: new_portee  = st.text_input("Portée max")
            with c3t: new_magasin = st.text_input("Magasin")
            with c4t: new_tir_r   = st.text_input("Tir/Rechargement")
        else:
            new_m_dist = new_portee = new_magasin = new_tir_r = ""

        if st.button("✅ Ajouter au catalogue"):
            if new_nom.strip():
                execute("""
                    INSERT INTO equipements
                        (categorie, sous_categorie, nom, poids_kg, prix_deniers, notes,
                         degats, mains, force_requise, resistance,
                         m_distance, portee_max, magasin, tir_rechargement)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    new_cat.strip(), new_sous.strip(), new_nom.strip(),
                    new_poids, new_prix, new_notes.strip(),
                    new_degats or None, new_mains or None,
                    new_force  or None, new_res   or None,
                    new_m_dist or None, new_portee or None,
                    new_magasin or None, new_tir_r or None,
                ))
                invalidate_cache()
                st.success(f"« {new_nom} » ajouté au catalogue !")
                st.rerun()
            else:
                st.warning("Le nom de l'objet est obligatoire.")

        st.markdown("---")
        st.markdown("#### Importer un fichier CSV ou Excel")
        st.caption("""
        **Format attendu (colonnes) :**
        Catégorie ; Sous-catégorie ; Nom ; Poids (Kg) ; Prix (Deniers) ; Notes ;
        Dégâts ; Mains ; Force requise ; Résistance ;
        M. distance ; Portée max ; Magasin ; Tir/Rechargement

        Tous les onglets d'un fichier Excel seront importés.
        Les colonnes absentes seront ignorées sans erreur.
        """)

        uploaded = st.file_uploader("Choisir un fichier CSV ou Excel", type=["csv", "xlsx", "xls"])
        if uploaded:
            try:
                import io
                col_map = {
                    "Catégorie":         "categorie",
                    "Sous-catégorie":    "sous_categorie",
                    "Nom":               "nom",
                    "Poids (Kg)":        "poids_kg",
                    "Prix (Deniers)":    "prix_deniers",
                    "Notes":             "notes",
                    "Dégâts":            "degats",
                    "Mains":             "mains",
                    "Force requise":     "force_requise",
                    "Résistance":        "resistance",
                    "M. distance":       "m_distance",
                    "Portée max":        "portee_max",
                    "Magasin":           "magasin",
                    "Tir/Rechargement":  "tir_rechargement",
                }

                filename = uploaded.name.lower()
                if filename.endswith(".csv"):
                    sheets = {"Feuille 1": pd.read_csv(uploaded, sep=";", encoding="latin-1")}
                else:
                    file_bytes = uploaded.read()
                    xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="calamine")
                    sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

                frames = []
                for sheet_name, df_sheet in sheets.items():
                    df_sheet = df_sheet.rename(columns=col_map)
                    if "nom" not in df_sheet.columns:
                        st.warning(f"Onglet « {sheet_name} » ignoré (colonne 'Nom' introuvable).")
                        continue
                    df_sheet = df_sheet.dropna(subset=["nom"])
                    df_sheet["_onglet"] = sheet_name
                    frames.append(df_sheet)

                if not frames:
                    st.error("Aucun onglet valide trouvé.")
                else:
                    df_import = pd.concat(frames, ignore_index=True)

                    if "poids_kg" in df_import.columns:
                        df_import["poids_kg"] = df_import["poids_kg"].astype(str).str.replace(",", ".").pipe(pd.to_numeric, errors="coerce").fillna(0.0)
                    else:
                        df_import["poids_kg"] = 0.0

                    if "prix_deniers" in df_import.columns:
                        df_import["prix_deniers"] = pd.to_numeric(df_import["prix_deniers"], errors="coerce").fillna(0).astype(int)
                    else:
                        df_import["prix_deniers"] = 0

                    for col in ["notes", "degats", "mains", "force_requise", "resistance",
                                "m_distance", "portee_max", "magasin", "tir_rechargement"]:
                        if col in df_import.columns:
                            df_import[col] = df_import[col].fillna("").astype(str).str.strip()
                            df_import[col] = df_import[col].replace("", None)
                        else:
                            df_import[col] = None

                    if "categorie" not in df_import.columns:
                        df_import["categorie"] = df_import["_onglet"]
                    if "sous_categorie" not in df_import.columns:
                        df_import["sous_categorie"] = ""

                    df_import = df_import.drop(columns=["_onglet"], errors="ignore")

                    st.markdown(f"**{len(df_import)} objets détectés** dans {len(frames)} onglet(s)")
                    st.dataframe(df_import.head(15), use_container_width=True)

                    all_cols = ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes",
                                "degats","mains","force_requise","resistance",
                                "m_distance","portee_max","magasin","tir_rechargement"]
                    keep = [c for c in all_cols if c in df_import.columns]

                    if st.button("📥 Importer tous les onglets dans la base"):
                        records = [tuple(r[c] for c in keep) for _, r in df_import.iterrows()]
                        cols_sql     = ", ".join(keep)
                        placeholders = ", ".join(["%s"] * len(keep))
                        executemany(f"INSERT INTO equipements ({cols_sql}) VALUES ({placeholders})", records)
                        invalidate_cache()
                        st.success(f"✅ {len(records)} objets importés avec succès !")
                        st.rerun()

            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier : {e}")

    # ── TAB 3 : Inventaires joueurs ──
    with tab3:
        players = load_players()
        if not players:
            st.info("Aucun joueur enregistré.")
        else:
            player_map = {p["username"]: p["id"] for p in players}
            selected_player = st.selectbox("Choisir un joueur", list(player_map.keys()))
            player_id = player_map[selected_player]

            pinfo = load_player_info(player_id)
            monture_j   = pinfo.get("monture") or "Aucune"
            poids_max_j = float(pinfo.get("poids_max_joueur") or 0)

            with st.expander(f"⚙️ Paramètres de {selected_player}", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    monture_idx = MONTURES.index(monture_j) if monture_j in MONTURES else 0
                    new_monture_j = st.selectbox("Type de monture", MONTURES, index=monture_idx, key="admin_monture")
                with c2:
                    new_poids_max_j = st.number_input("Poids max sur soi (kg)", min_value=0.0,
                                                       value=poids_max_j, step=0.5, format="%.1f", key="admin_poids_max")
                if st.button("💾 Sauvegarder les paramètres", key="admin_save_params"):
                    execute("UPDATE users SET monture=%s, poids_max_joueur=%s WHERE id=%s",
                            (new_monture_j, new_poids_max_j, player_id))
                    invalidate_cache()
                    st.success(f"Paramètres de {selected_player} mis à jour.")
                    st.rerun()

            df_inv = load_inventory(player_id)
            if df_inv.empty:
                st.info(f"{selected_player} ne possède aucun objet.")
            else:
                df_inv["poids_total"] = df_inv["poids_kg"] * df_inv["quantite"]
                df_soi  = df_inv[df_inv["localisation"] == "soi"]
                df_mont = df_inv[df_inv["localisation"] == "monture"]
                poids_soi  = df_soi["poids_total"].sum()
                poids_mont = df_mont["poids_total"].sum()

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""<div class="metric-card">
                        <div class="metric-value">{len(df_inv)}</div>
                        <div class="metric-label">Objets différents</div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    couleur = "#c0392b" if poids_max_j > 0 and poids_soi > poids_max_j else "#b8860b"
                    st.markdown(f"""<div class="metric-card">
                        <div class="metric-value" style="color:{couleur}">{poids_soi:.2f} kg</div>
                        <div class="metric-label">Sur soi{f" / {poids_max_j:.1f} max" if poids_max_j > 0 else ""}</div>
                    </div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class="metric-card">
                        <div class="metric-value">{poids_mont:.2f} kg</div>
                        <div class="metric-label">Sur {monture_j if monture_j != "Aucune" else "monture"}</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")

                def _afficher_inventaire_section(df_section: pd.DataFrame, label_icon: str):
                    for cat in sorted(df_section["categorie"].dropna().unique()):
                        df_c = df_section[df_section["categorie"] == cat].copy()
                        df_c["poids_total"] = df_c["poids_kg"] * df_c["quantite"]
                        mask_tir  = df_c["sous_categorie"].apply(is_tir)
                        df_c_mel  = df_c[~mask_tir]
                        df_c_tir  = df_c[mask_tir]

                        with st.expander(f"{label_icon} {cat}  •  {df_c['poids_total'].sum():.2f} kg", expanded=False):
                            if not df_c_mel.empty:
                                st.markdown("*Mêlée*")
                                cols_m, ren_m = _cols_display_melee(df_c_mel)
                                extra_inv = ["quantite", "poids_total", "localisation"]
                                cols_show = [c for c in extra_inv + cols_m if c in df_c_mel.columns]
                                ren_m.update({"quantite":"Qté","poids_total":"Poids total","localisation":"Lieu"})
                                st.dataframe(df_c_mel[cols_show].rename(columns=ren_m), use_container_width=True, hide_index=True)
                            if not df_c_tir.empty:
                                st.markdown("*Tir*")
                                cols_t, ren_t = _cols_display_tir(df_c_tir)
                                extra_inv = ["quantite", "poids_total", "localisation"]
                                cols_show = [c for c in extra_inv + cols_t if c in df_c_tir.columns]
                                ren_t.update({"quantite":"Qté","poids_total":"Poids total","localisation":"Lieu"})
                                st.dataframe(df_c_tir[cols_show].rename(columns=ren_t), use_container_width=True, hide_index=True)

                st.markdown("**🧍 Sur soi**")
                if df_soi.empty:
                    st.caption("Aucun objet sur soi.")
                else:
                    _afficher_inventaire_section(df_soi, "⚔️")

                if monture_j != "Aucune":
                    st.markdown(f"**🐴 Sur la {monture_j}**")
                    if df_mont.empty:
                        st.caption(f"Aucun objet sur la {monture_j}.")
                    else:
                        _afficher_inventaire_section(df_mont, "🐴")

                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 🔀 Déplacer un objet")
                    obj_move = st.selectbox("Objet à déplacer", df_inv["nom"].tolist(), key="admin_move")
                    loc_act  = df_inv[df_inv["nom"] == obj_move]["localisation"].values[0]
                    new_loc  = "monture" if loc_act == "soi" else "soi"
                    lbl      = f"➡️ Mettre sur la {monture_j}" if new_loc == "monture" else "➡️ Mettre sur soi"
                    if monture_j != "Aucune" or new_loc == "soi":
                        if st.button(lbl, key="admin_move_btn"):
                            inv_id = int(df_inv[df_inv["nom"] == obj_move]["inv_id"].values[0])
                            execute("UPDATE inventaire SET localisation=%s WHERE id=%s", (new_loc, inv_id))
                            invalidate_cache()
                            st.rerun()
                with c2:
                    st.markdown("##### 🗑️ Retirer un objet de l'inventaire")
                    to_remove = st.selectbox("Objet à retirer", df_inv["nom"].tolist(), key="admin_remove")
                    if st.button("🗑️ Retirer", key="admin_remove_btn"):
                        inv_id = int(df_inv[df_inv["nom"] == to_remove]["inv_id"].values[0])
                        execute("DELETE FROM inventaire WHERE id=%s", (inv_id,))
                        invalidate_cache()
                        st.success(f"« {to_remove} » retiré de l'inventaire de {selected_player}.")
                        st.rerun()

            st.markdown("---")
            st.markdown("##### Ajouter un objet à l'inventaire")
            df_eq = load_equipements()
            if not df_eq.empty:
                c1, c2, c3 = st.columns(3)
                with c1:
                    cats = ["Toutes"] + sorted(df_eq["categorie"].dropna().unique().tolist())
                    add_cat = st.selectbox("Catégorie", cats, key="admin_add_cat")
                with c2:
                    sub_df = df_eq[df_eq["categorie"] == add_cat] if add_cat != "Toutes" else df_eq
                    sous = ["Toutes"] + sorted(sub_df["sous_categorie"].dropna().unique().tolist())
                    add_sous = st.selectbox("Sous-catégorie", sous, key="admin_add_sous")
                with c3:
                    qty = st.number_input("Quantité", min_value=1, max_value=99, value=1, key="admin_add_qty")

                filtered_eq = df_eq.copy()
                if add_cat  != "Toutes": filtered_eq = filtered_eq[filtered_eq["categorie"]      == add_cat]
                if add_sous != "Toutes": filtered_eq = filtered_eq[filtered_eq["sous_categorie"] == add_sous]

                c1, c2 = st.columns(2)
                with c1:
                    chosen_eq = st.selectbox("Choisir l'objet", sorted(filtered_eq["nom"].tolist()), key="admin_add_eq")
                with c2:
                    monture_cur = load_player_info(player_id).get("monture") or "Aucune"
                    loc_opts    = ["soi"] + (["monture"] if monture_cur != "Aucune" else [])
                    loc_lbls    = ["🧍 Sur soi"] + ([f"🐴 Sur la {monture_cur}"] if monture_cur != "Aucune" else [])
                    loc_ch      = st.selectbox("Ranger où ?", loc_lbls, key="admin_add_loc")
                    loc_v       = loc_opts[loc_lbls.index(loc_ch)]

                if st.button("➕ Ajouter à l'inventaire"):
                    eq_id = int(df_eq[df_eq["nom"] == chosen_eq]["id"].values[0])
                    execute(
                        "INSERT INTO inventaire (player_id, equipement_id, quantite, localisation) VALUES (%s, %s, %s, %s)",
                        (player_id, eq_id, qty, loc_v)
                    )
                    invalidate_cache()
                    st.success(f"« {chosen_eq} » (x{qty}) ajouté à l'inventaire de {selected_player} — {loc_ch}.")
                    st.rerun()

    # ── TAB 4 : Gestion joueurs ──
    with tab4:
        st.markdown("#### Créer un compte joueur")
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Nom d'utilisateur", key="new_user")
        with c2:
            new_password = st.text_input("Mot de passe", type="password", key="new_pass")

        if st.button("👤 Créer le compte"):
            if new_username.strip() and new_password.strip():
                try:
                    execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'joueur')",
                        (new_username.strip(), hash_password(new_password))
                    )
                    invalidate_cache()
                    st.success(f"Compte joueur « {new_username} » créé.")
                except Exception as e:
                    st.error(f"Erreur (nom déjà pris ?) : {e}")
            else:
                st.warning("Nom d'utilisateur et mot de passe requis.")

        st.markdown("---")
        st.markdown("#### Joueurs enregistrés")
        players = load_players()
        if players:
            for p in players:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"🧙 **{p['username']}**")
                with c2:
                    if st.button("Supprimer", key=f"del_{p['id']}"):
                        execute("DELETE FROM users WHERE id=%s", (p["id"],))
                        invalidate_cache()
                        st.rerun()
        else:
            st.info("Aucun joueur enregistré.")

# ─────────────────────────────────────────────
#  PAGE : JOUEUR
# ─────────────────────────────────────────────
def page_joueur():
    user = st.session_state.user
    st.markdown(f"""
    <div class="banner">
        <h1>🐉 Rêve de Dragon</h1>
        <p>Carnet d'aventurier de <em>{user['username']}</em></p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎒 Mon inventaire", "⚔️ Catalogue"])

    with tab1:
        pinfo = load_player_info(user["id"])
        monture_actuelle = pinfo.get("monture") or "Aucune"
        poids_max        = float(pinfo.get("poids_max_joueur") or 0)

        with st.expander("⚙️ Paramètres du personnage", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                monture_idx = MONTURES.index(monture_actuelle) if monture_actuelle in MONTURES else 0
                new_monture = st.selectbox("Type de monture", MONTURES, index=monture_idx, key="j_monture")
            with c2:
                new_poids_max = st.number_input("Poids max sur soi (kg)", min_value=0.0,
                                                 value=poids_max, step=0.5, format="%.1f", key="j_poids_max")
            if st.button("💾 Sauvegarder", key="j_save_params"):
                execute("UPDATE users SET monture=%s, poids_max_joueur=%s WHERE id=%s",
                        (new_monture, new_poids_max, user["id"]))
                invalidate_cache()
                st.success("Paramètres sauvegardés !")
                st.rerun()

        df_inv = load_inventory(user["id"])

        if df_inv.empty:
            st.info("Votre besace est vide. Consultez le catalogue pour vous équiper.")
        else:
            df_inv["poids_total"]  = df_inv["poids_kg"] * df_inv["quantite"]
            df_soi     = df_inv[df_inv["localisation"] == "soi"]
            df_monture = df_inv[df_inv["localisation"] == "monture"]
            poids_soi     = df_soi["poids_total"].sum()
            poids_monture = df_monture["poids_total"].sum()
            poids_total   = df_inv["poids_total"].sum()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{len(df_inv)}</div>
                    <div class="metric-label">Types d'objets</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                couleur_poids = "#c0392b" if poids_max > 0 and poids_soi > poids_max else "#b8860b"
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value" style="color:{couleur_poids}">{poids_soi:.2f} kg</div>
                    <div class="metric-label">Sur soi{f" / {poids_max:.1f} kg max" if poids_max > 0 else ""}</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                monture_label = monture_actuelle if monture_actuelle != "Aucune" else "—"
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{poids_monture:.2f} kg</div>
                    <div class="metric-label">Sur {monture_label}</div>
                </div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{poids_total:.2f} kg</div>
                    <div class="metric-label">Poids total</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")

            def _section_joueur(df_section: pd.DataFrame, titre: str):
                st.markdown(f"### {titre}")
                if df_section.empty:
                    st.caption("Aucun objet.")
                    return
                for cat in sorted(df_section["categorie"].dropna().unique()):
                    df_cat = df_section[df_section["categorie"] == cat].copy()
                    df_cat["poids_total"] = df_cat["poids_kg"] * df_cat["quantite"]
                    nb_cat    = df_cat["quantite"].sum()
                    poids_cat = df_cat["poids_total"].sum()

                    mask_tir = df_cat["sous_categorie"].apply(is_tir)
                    df_mel   = df_cat[~mask_tir]
                    df_tir_c = df_cat[mask_tir]

                    with st.expander(f"⚔️ {cat}  —  {int(nb_cat)} objet(s)  •  {poids_cat:.2f} kg", expanded=True):
                        if not df_mel.empty:
                            st.markdown("**Mêlée**")
                            cols_m, ren_m = _cols_display_melee(df_mel)
                            base_inv = ["nom","quantite","poids_kg","poids_total","sous_categorie","notes"]
                            stat_cols = [c for c in COLS_ARMES_COMMUNES if c in df_mel.columns]
                            show = [c for c in base_inv + stat_cols if c in df_mel.columns]
                            ren_m.update({"nom":"Objet","quantite":"Quantité","poids_kg":"Poids unit. (kg)","poids_total":"Poids total (kg)","sous_categorie":"Sous-catégorie"})
                            st.dataframe(df_mel[show].rename(columns=ren_m), use_container_width=True, hide_index=True)

                        if not df_tir_c.empty:
                            st.markdown("**Tir**")
                            cols_t, ren_t = _cols_display_tir(df_tir_c)
                            base_inv = ["nom","quantite","poids_kg","poids_total","sous_categorie","notes"]
                            stat_cols = [c for c in ["degats"] + COLS_ARMES_TIR if c in df_tir_c.columns]
                            show = [c for c in base_inv + stat_cols if c in df_tir_c.columns]
                            ren_t.update({"nom":"Objet","quantite":"Quantité","poids_kg":"Poids unit. (kg)","poids_total":"Poids total (kg)","sous_categorie":"Sous-catégorie"})
                            st.dataframe(df_tir_c[show].rename(columns=ren_t), use_container_width=True, hide_index=True)

            _section_joueur(df_soi,     "🧍 Sur soi")
            if monture_actuelle != "Aucune":
                _section_joueur(df_monture, f"🐴 Sur la {monture_actuelle}")

            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 🔀 Déplacer un objet")
                obj_deplacer = st.selectbox("Objet à déplacer", df_inv["nom"].tolist(), key="j_move")
                loc_actuelle = df_inv[df_inv["nom"] == obj_deplacer]["localisation"].values[0]
                nouvelle_loc = "monture" if loc_actuelle == "soi" else "soi"
                dest_label   = f"➡️ Mettre sur la {monture_actuelle}" if nouvelle_loc == "monture" else "➡️ Mettre sur soi"
                if monture_actuelle != "Aucune" or nouvelle_loc == "soi":
                    if st.button(dest_label, key="j_move_btn"):
                        inv_id = int(df_inv[df_inv["nom"] == obj_deplacer]["inv_id"].values[0])
                        execute("UPDATE inventaire SET localisation=%s WHERE id=%s", (nouvelle_loc, inv_id))
                        invalidate_cache()
                        st.rerun()
                else:
                    st.caption("Définissez d'abord une monture dans les paramètres.")
            with c2:
                st.markdown("##### 🗑️ Retirer un objet")
                to_remove = st.selectbox("Objet à retirer", df_inv["nom"].tolist(), key="j_remove")
                if st.button("🗑️ Retirer de mon inventaire", key="j_remove_btn"):
                    inv_id = int(df_inv[df_inv["nom"] == to_remove]["inv_id"].values[0])
                    execute("DELETE FROM inventaire WHERE id=%s", (inv_id,))
                    invalidate_cache()
                    st.success(f"« {to_remove} » retiré de votre inventaire.")
                    st.rerun()

    with tab2:
        df = load_equipements()
        afficher_catalogue(df, key_prefix="joueur_cat")

        st.markdown("---")
        st.markdown("##### Ajouter un objet à mon inventaire")
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            with c1:
                eq_list   = sorted(df["nom"].tolist())
                chosen_eq = st.selectbox("Choisir l'objet", eq_list, key="jadd_eq")
            with c2:
                qty = st.number_input("Quantité", min_value=1, max_value=99, value=1, key="jadd_qty")
            with c3:
                pinfo2   = load_player_info(user["id"])
                monture2 = pinfo2.get("monture") or "Aucune"
                loc_options = ["soi"] + (["monture"] if monture2 != "Aucune" else [])
                loc_labels  = ["🧍 Sur soi"] + ([f"🐴 Sur la {monture2}"] if monture2 != "Aucune" else [])
                loc_choice  = st.selectbox("Ranger où ?", loc_labels, key="jadd_loc")
                loc_val     = loc_options[loc_labels.index(loc_choice)]

            if st.button("➕ Ajouter à mon inventaire"):
                eq_id = int(df[df["nom"] == chosen_eq]["id"].values[0])
                execute(
                    "INSERT INTO inventaire (player_id, equipement_id, quantite, localisation) VALUES (%s, %s, %s, %s)",
                    (user["id"], eq_id, qty, loc_val)
                )
                invalidate_cache()
                st.success(f"« {chosen_eq} » (x{qty}) ajouté — {loc_choice} !")
                st.rerun()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🐉 Navigation")
    st.markdown("---")
    if st.session_state.user:
        u = st.session_state.user
        role_tag = "Maître des Rêves" if u["role"] == "admin" else "Aventurier"
        st.markdown(f"**{u['username']}**")
        st.markdown(f'<span class="tag">{role_tag}</span>', unsafe_allow_html=True)
        st.markdown("")
        if st.button("🚪 Se déconnecter"):
            st.session_state.user = None
            st.rerun()

# ─────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────
if st.session_state.user is None:
    page_login()
elif st.session_state.user["role"] == "admin":
    page_admin()
else:
    page_joueur()
