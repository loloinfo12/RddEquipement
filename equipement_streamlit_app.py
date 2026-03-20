import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from contextlib import contextmanager
import requests
import re
import io

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
.stDownloadButton > button {
    background: var(--blood) !important;
    color: var(--parchment) !important;
    border: 1px solid var(--gold) !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    border-radius: 2px !important;
    transition: all 0.2s;
    width: 100%;
}
.stDownloadButton > button:hover {
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
input[type="text"], input[type="password"], input[type="number"],
input[type="email"], input {
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
COLS_ARMES_LANCER   = ["m_distance", "portee_max"]

# ─────────────────────────────────────────────
#  TABLE DE CANONISATION DES SOUS-CATÉGORIES
# ─────────────────────────────────────────────
_CANON_TABLE: dict[str, str] = {
    # ── Armes de tir ──
    "arbalète": "Arbalètes", "arbalètes": "Arbalètes",
    "arc": "Arcs", "arcs": "Arcs",
    "arme de poing": "Armes de poing", "armes de poing": "Armes de poing",
    "arme d'épaule": "Armes d'épaule", "armes d'épaule": "Armes d'épaule",
    "fronde": "Frondes", "frondes": "Frondes",
    "sarbacane": "Sarbacanes", "sarbacanes": "Sarbacanes",
    # ── Armes de lancer ──
    "arme de lancer": "Armes de lancer", "armes de lancer": "Armes de lancer",
    # ── Épées ──
    "épée": "Épées", "épées": "Épées", "epée": "Épées", "epées": "Épées",
    "épée à une main": "Épées à une main", "épées à une main": "Épées à une main",
    "epée à une main": "Épées à une main", "epées à une main": "Épées à une main",
    "épée à deux mains": "Épées à deux mains", "épées à deux mains": "Épées à deux mains",
    "epée à deux mains": "Épées à deux mains", "epées à deux mains": "Épées à deux mains",
    # ── Haches ──
    "hache": "Haches à une main", "haches": "Haches à une main",
    "hache à une main": "Haches à une main", "haches à une main": "Haches à une main",
    "hache à deux mains": "Haches à deux mains", "haches à deux mains": "Haches à deux mains",
    # ── Masses ──
    "masse": "Masses", "masses": "Masses",
    "masse à une main": "Masses à une main", "masses à une main": "Masses à une main",
    "masse à deux mains": "Masses à deux mains", "masses à deux mains": "Masses à deux mains",
    "massette": "Masses", "massettes": "Masses",
    "marteau": "Masses", "marteaux": "Masses",
    "marteau de guerre": "Masses", "marteaux de guerre": "Masses",
    # ── Autres mêlée ──
    "lance": "Lances", "lances": "Lances",
    "dague": "Dagues", "dagues": "Dagues",
    "bâton": "Bâtons", "bâtons": "Bâtons",
    "fléau": "Fléaux", "fléaux": "Fléaux",
    "fouet": "Fouets", "fouets": "Fouets",
    "estoc": "Épées à une main", "estocs": "Épées à une main",
    "cimeterre": "Épées à une main", "cimeterres": "Épées à une main",
    "sabre": "Épées à une main", "sabres": "Épées à une main",
    "claymore": "Épées à deux mains", "claymores": "Épées à deux mains",
    "hallebarde": "Lances", "hallebardes": "Lances",
    "pique": "Lances", "piques": "Lances",
    "matériel de siège": "Matériel de siège",
    # ── Armes d'hast ──
    "arme d'hast": "Armes d'hast", "armes d'hast": "Armes d'hast",
    "arme dhast": "Armes d'hast", "armes dhast": "Armes d'hast",
    "bardiche": "Armes d'hast", "bardiches": "Armes d'hast",
    "bec de corbin": "Armes d'hast", "becs de corbin": "Armes d'hast",
    "doloire": "Armes d'hast", "doloires": "Armes d'hast",
    "doloire-guisarme": "Armes d'hast",
    "esponton": "Armes d'hast", "espontons": "Armes d'hast",
    "fauchard": "Armes d'hast", "fauchards": "Armes d'hast",
    "fauchard-crochet": "Armes d'hast",
    "fourche": "Armes d'hast", "fourches": "Armes d'hast",
    "fourche-fauchard": "Armes d'hast",
    "guisarme": "Armes d'hast", "guisarmes": "Armes d'hast",
    "autre": "Autre",
}

def canoniser_sous_cat(s: str) -> str:
    return _CANON_TABLE.get(str(s).strip().lower(), s)

def _appliquer_canon(df: "pd.DataFrame") -> "pd.DataFrame":
    if not df.empty and "sous_categorie" in df.columns:
        df = df.copy()
        df["sous_categorie"] = df["sous_categorie"].apply(
            lambda x: canoniser_sous_cat(str(x)) if x else x
        )
    return df

SOUS_CAT_TIR    = {"Arbalètes", "Arcs", "Armes de poing", "Armes d'épaule", "Frondes", "Sarbacanes"}
SOUS_CAT_LANCER = {"Armes de lancer"}
SOUS_CAT_MELEE  = {
    "Épées", "Épées à une main", "Épées à deux mains",
    "Haches à une main", "Haches à deux mains",
    "Masses", "Masses à une main", "Masses à deux mains",
    "Lances", "Dagues", "Bâtons", "Fléaux", "Fouets",
    "Armes d'hast", "Matériel de siège", "Autre",
}
SOUS_CATS_ARMES = SOUS_CAT_TIR | SOUS_CAT_LANCER | SOUS_CAT_MELEE

TOUTES_SOUS_CATEGORIES = sorted([
    "Arbalètes", "Arcs", "Armes de poing", "Armes d'épaule", "Frondes", "Sarbacanes",
    "Armes de lancer",
    "Épées", "Épées à une main", "Épées à deux mains",
    "Haches à une main", "Haches à deux mains",
    "Masses", "Masses à une main", "Masses à deux mains",
    "Lances", "Dagues", "Bâtons", "Fléaux", "Fouets",
    "Armes d'hast", "Matériel de siège", "Autre",
])

LABELS_COMMUNES = {"degats":"Dégâts","mains":"Mains","force_requise":"Force requise","resistance":"Résistance"}
LABELS_TIR      = {"m_distance":"M. distance","portee_max":"Portée max","magasin":"Magasin","tir_rechargement":"Tir/Rechargement"}
LABELS_LANCER   = {"m_distance":"M. distance","portee_max":"Portée max"}

def is_tir(sous_categorie: str) -> bool:
    return canoniser_sous_cat(sous_categorie) in SOUS_CAT_TIR

def is_lancer(sous_categorie: str) -> bool:
    return canoniser_sous_cat(sous_categorie) in SOUS_CAT_LANCER

def is_arme(sous_categorie: str) -> bool:
    return canoniser_sous_cat(sous_categorie) in SOUS_CATS_ARMES

# ─────────────────────────────────────────────
#  CONNEXION NEON
# ─────────────────────────────────────────────
@contextmanager
def get_conn():
    conn = psycopg2.connect(st.secrets["DATABASE_URL"], cursor_factory=RealDictCursor)
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
    rows = query("SELECT * FROM users WHERE username=%s AND password_hash=%s",
                 (username, hash_password(password)))
    return dict(rows[0]) if rows else None

# ─────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_equipements() -> pd.DataFrame:
    rows = query("""SELECT id, categorie, sous_categorie, nom, poids_kg, prix_deniers, notes,
                           degats, mains, force_requise, resistance, m_distance, portee_max,
                           magasin, tir_rechargement, svg_illustration
                    FROM equipements ORDER BY categorie, sous_categorie, nom""")
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    return _appliquer_canon(df)

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
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    return _appliquer_canon(df)

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
#  ENCOMBREMENT  (1 enc = 2 kg)
# ─────────────────────────────────────────────
ENC_PAR_KG = 0.5  # facteur : kg → enc

def enc(kg) -> str:
    """Convertit des kg en points d'encombrement affichables."""
    try:
        val = float(kg or 0) * ENC_PAR_KG
    except (TypeError, ValueError):
        val = 0.0
    if val == 0:
        return "0"
    return str(int(val)) if val == int(val) else f"{val:.1f}"

def enc_val(kg) -> float:
    """Retourne la valeur numérique en enc."""
    try:
        return float(kg or 0) * ENC_PAR_KG
    except (TypeError, ValueError):
        return 0.0

# ─────────────────────────────────────────────
#  GÉNÉRATION PDF FICHE ÉQUIPEMENT
# ─────────────────────────────────────────────
def generer_fiche_pdf(nom_perso: str, df_inv: pd.DataFrame, monture: str, poids_max: float) -> bytes:
    """Génère la fiche d'équipement RdD pré-remplie. Retourne les bytes du PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    W, H = A4
    ENCRE     = colors.HexColor("#2c1a0e")
    ROUGE     = colors.HexColor("#8b1a1a")
    OR        = colors.HexColor("#b8860b")
    PARCHEMIN = colors.HexColor("#f5ead0")
    GRIS_L    = colors.HexColor("#d9cdb0")
    ENCRE_L   = colors.HexColor("#5c3a1e")

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Rêve de Dragon – Fiche Équipement – {nom_perso}")

    # Fond parchemin + bordure
    c.setFillColor(PARCHEMIN)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(ENCRE)
    c.setLineWidth(1.2)
    c.rect(8*mm, 8*mm, W - 16*mm, H - 16*mm, fill=0, stroke=1)

    # ── Entête ──
    c.setFillColor(ROUGE)
    c.setFont("Times-BoldItalic", 26)
    c.drawString(12*mm, H - 21*mm, "Rêve")
    c.setFont("Times-Bold", 13)
    c.drawString(12*mm, H - 28*mm, "de Dragon")
    c.setFillColor(ENCRE)
    c.setFont("Times-Bold", 15)
    c.drawString(12*mm, H - 39*mm, "EQUIPEMENT")
    c.setLineWidth(0.8)
    c.setStrokeColor(ENCRE)
    c.line(12*mm, H - 40.5*mm, 73*mm, H - 40.5*mm)

    # Nom personnage
    c.setFont("Times-BoldItalic", 20)
    c.setFillColor(ENCRE)
    c.drawString(82*mm, H - 19*mm, nom_perso)
    c.setLineWidth(0.7)
    c.line(82*mm, H - 21*mm, W - 12*mm, H - 21*mm)
    c.setFont("Times-Roman", 6.5)
    c.setFillColor(ENCRE_L)
    c.drawString(82*mm, H - 24*mm, "NOM DU PERSONNAGE")

    if monture and monture != "Aucune":
        c.setFont("Times-Italic", 7.5)
        c.setFillColor(ENCRE_L)
        c.drawString(82*mm, H - 30*mm, f"Monture : {monture}")
    if poids_max > 0:
        c.setFont("Times-Italic", 7.5)
        c.setFillColor(ENCRE_L)
        c.drawString(140*mm, H - 30*mm, f"Enc. max sur soi : {enc_val(poids_max):.1f} enc.")

    c.setStrokeColor(ENCRE)
    c.setLineWidth(1.2)
    c.line(12*mm, H - 45*mm, W - 12*mm, H - 45*mm)

    # ── Layout ──
    col_a = 12*mm
    col_b = 75*mm
    col_c = 138*mm
    col_w = 56*mm
    top   = H - 49*mm
    LH    = 5*mm

    def section_titre(x, y, label, annot=""):
        c.setFillColor(ENCRE)
        c.setFont("Times-Bold", 7.5)
        c.setStrokeColor(ENCRE)
        c.setLineWidth(0.6)
        c.rect(x, y - 4*mm, col_w, 5*mm, fill=0, stroke=1)
        c.drawString(x + 1.5*mm, y - 2.5*mm, label)
        if annot:
            c.setFont("Times-Roman", 6)
            c.setFillColor(ENCRE_L)
            c.drawRightString(x + col_w - 1*mm, y - 2*mm, annot)
        return y - 5*mm

    def ligne_item(x, y, texte="", droite="", largeur=None):
        lw = largeur or col_w
        c.setStrokeColor(GRIS_L)
        c.setLineWidth(0.4)
        c.line(x, y, x + lw, y)
        if texte:
            c.setFont("Times-Italic", 7.5)
            c.setFillColor(ENCRE)
            max_chars = max(10, int(lw / (1.9*mm)) - 2)
            txt = texte[:max_chars] if len(texte) > max_chars else texte
            c.drawString(x + 1*mm, y + 1*mm, txt)
        if droite:
            c.setFont("Times-Roman", 7)
            c.setFillColor(ENCRE)
            c.drawRightString(x + lw - 1*mm, y + 1*mm, str(droite))
        return y - LH

    def lignes_vides(x, y, n, largeur=None):
        for _ in range(n):
            y = ligne_item(x, y, largeur=largeur)
        return y

    # ── Préparer données inventaire ──
    if not df_inv.empty:
        df_inv = df_inv.copy()
        df_inv["poids_total"] = df_inv["poids_kg"] * df_inv["quantite"]
        df_soi     = df_inv[df_inv["localisation"] == "soi"].copy()
        df_monture = df_inv[df_inv["localisation"] == "monture"].copy()
    else:
        df_soi = df_monture = pd.DataFrame()

    def rows_to_lines(df_sub, max_n, show_poids=True):
        lines = []
        for _, row in df_sub.iterrows():
            nom_it = str(row.get("nom", ""))
            qty    = int(row.get("quantite", 1))
            poids  = row.get("poids_total", 0) or 0
            label  = f"{nom_it} x{qty}" if qty > 1 else nom_it
            poids_s = enc(poids) if (show_poids and poids > 0) else ""
            lines.append((label, poids_s))
        while len(lines) < max_n:
            lines.append(("", ""))
        return lines[:max_n]

    def rows_armes(df_sub, max_n):
        lines = []
        for _, row in df_sub.iterrows():
            nom_it = str(row.get("nom", ""))
            qty    = int(row.get("quantite", 1))
            degats = str(row.get("degats", "") or "")
            res    = str(row.get("resistance", "") or "")
            poids  = row.get("poids_total", 0) or 0
            label  = f"{nom_it} x{qty}" if qty > 1 else nom_it
            stat   = "  ".join(filter(None, [degats, res, enc(poids) + " enc." if poids else ""]))
            lines.append((label, stat))
        while len(lines) < max_n:
            lines.append(("", ""))
        return lines[:max_n]

    def rows_armures(df_sub, max_n):
        lines = []
        for _, row in df_sub.iterrows():
            nom_it = str(row.get("nom", ""))
            prot   = str(row.get("degats", "") or "")
            det    = str(row.get("resistance", "") or "")
            stat   = "  ".join(filter(None, [prot, det]))
            lines.append((nom_it, stat))
        while len(lines) < max_n:
            lines.append(("", ""))
        return lines[:max_n]

    poids_soi_total  = float(df_soi["poids_total"].sum())  if not df_soi.empty  else 0.0
    poids_mont_total = float(df_monture["poids_total"].sum()) if not df_monture.empty else 0.0
    poids_total      = poids_soi_total + poids_mont_total
    monture_label    = monture if (monture and monture != "Aucune") else "Monture"

    # ══ COLONNE A : Sur soi ══
    y_a = top
    y_a = section_titre(col_a, y_a, "Porté sur soi", "Enc.")
    lines_soi = rows_to_lines(df_soi, 11)
    for txt, po in lines_soi:
        y_a = ligne_item(col_a, y_a, txt, po)
    y_a -= 3*mm

    y_a = section_titre(col_a, y_a, "Sac à dos / Divers", "Enc.")
    lines_sac = rows_to_lines(df_soi, 14)
    for txt, po in lines_sac:
        y_a = ligne_item(col_a, y_a, txt, po)
    y_a -= 2*mm
    c.setFont("Times-Bold", 8)
    c.setFillColor(ENCRE)
    c.drawString(col_a, y_a, "Enc. sur soi :")
    c.setFont("Times-Bold", 9)
    c.setFillColor(ROUGE if poids_max > 0 and poids_soi_total > poids_max else OR)
    c.drawRightString(col_a + col_w, y_a, f"{enc_val(poids_soi_total):.1f} enc.")

    # ══ COLONNE B : Sur la monture ══
    y_b = top
    y_b = section_titre(col_b, y_b, f"Sur la {monture_label}", "Enc.")
    lines_mont = rows_to_lines(df_monture, 20) if not df_monture.empty else [("", "")] * 20
    for txt, po in lines_mont:
        y_b = ligne_item(col_b, y_b, txt, po)
    y_b -= 2*mm
    c.setFont("Times-Bold", 8)
    c.setFillColor(ENCRE)
    c.drawString(col_b, y_b, f"Enc. {monture_label} :")
    c.setFont("Times-Bold", 9)
    c.setFillColor(OR)
    c.drawRightString(col_b + col_w, y_b, f"{enc_val(poids_mont_total):.1f} enc.")

    # ══ COLONNE C : Armes / Armures / Récap ══
    y_c = top
    df_armes   = df_inv[df_inv["sous_categorie"].apply(is_arme)]  if not df_inv.empty else pd.DataFrame()
    df_armures = df_inv[df_inv["categorie"].str.lower().str.contains("armure", na=False)] if not df_inv.empty else pd.DataFrame()

    y_c = section_titre(col_c, y_c, "Armes", "+dom  rés.  enc.")
    for txt, stat in rows_armes(df_armes, 7):
        y_c = ligne_item(col_c, y_c, txt, stat)
    y_c -= 4*mm

    y_c = section_titre(col_c, y_c, "Armures", "prot.  déter.")
    for txt, stat in rows_armures(df_armures, 5):
        y_c = ligne_item(col_c, y_c, txt, stat)
    y_c -= 4*mm

    y_c = section_titre(col_c, y_c, "Récapitulatif poids", "")
    recap = [
        (f"Sur soi : {enc_val(poids_soi_total):.1f} enc.", f"/ {enc_val(poids_max):.1f} max" if poids_max > 0 else ""),
        (f"Sur {monture_label} : {enc_val(poids_mont_total):.1f} enc.", ""),
        (f"Total : {enc_val(poids_total):.1f} enc.", ""),
    ]
    for txt, po in recap:
        y_c = ligne_item(col_c, y_c, txt, po)
    y_c = lignes_vides(col_c, y_c, 3)
    y_c -= 4*mm

    y_c = section_titre(col_c, y_c, "Notes", "")
    y_c = lignes_vides(col_c, y_c, 10)

    # Séparateurs verticaux
    c.setStrokeColor(colors.HexColor("#c8b99a"))
    c.setLineWidth(0.5)
    c.line(col_b - 3*mm, H - 45*mm, col_b - 3*mm, 20*mm)
    c.line(col_c - 3*mm, H - 45*mm, col_c - 3*mm, 20*mm)

    # Enc. total global
    c.setStrokeColor(ENCRE)
    c.setLineWidth(1)
    c.line(12*mm, 22*mm, W - 12*mm, 22*mm)
    c.setFont("Times-BoldItalic", 13)
    c.setFillColor(ENCRE)
    c.drawString(col_c, 13*mm, "Enc. total")
    c.setFont("Times-Bold", 13)
    c.setFillColor(OR)
    c.drawRightString(W - 12*mm, 13*mm, f"{enc_val(poids_total):.1f} enc.")

    c.save()
    buf.seek(0)
    return buf.read()


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
        resp = requests.get(url, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; RDD-App/1.0)"},
                            allow_redirects=True)
        if resp.status_code != 200:
            return None
        mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        if not mime.startswith("image/"):
            mime = "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(resp.content).decode()}"
    except Exception:
        return None

def generer_svg_arme(nom: str, sous_categorie: str, notes: str, degats: str = "") -> str | None:
    prompt = f"""Tu es un illustrateur médiéval spécialisé dans les armes fantasy.
Crée un SVG 300×400 illustrant cette arme de manière artistique, dans un style gravure médiévale sur parchemin clair.

Arme : {nom}
Catégorie : {sous_categorie}
Description : {notes}
Dégâts : {degats or "non précisé"}

Règles ABSOLUES :
- SVG viewBox="0 0 300 400" xmlns="http://www.w3.org/2000/svg"
- FOND OBLIGATOIRE : <rect width="300" height="400" fill="#f5ead0"/>
- stroke="#2c1a0e", fill="none" ou fill="#2c1a0e"
- JAMAIS de couleurs sombres pour le fond
- L'arme occupe AU MINIMUM 80% de la surface
- Centre sur x=150, y=180
- Incline légèrement (rotate 10°-30°)
- En bas (y=375) : nom centré, font-family="serif", fill="#b8860b", font-size="13"
- Renvoie UNIQUEMENT le code SVG brut"""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":st.secrets["ANTHROPIC_API_KEY"],"anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":4000,"messages":[{"role":"user","content":prompt}]},
            timeout=60
        )
        data = resp.json()
        text = "".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text")
        match = re.search(r'(<svg[\s\S]*?</svg>)', text, re.IGNORECASE)
        return match.group(1) if match else text.strip()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None

def _afficher_image_stockee(data_uri: str, nom: str):
    if data_uri.startswith("data:image/"):
        st.markdown(f"""<div style="border:2px solid #b8860b;border-radius:6px;padding:8px;
                    background:#1a0f05;display:flex;justify-content:center;">
            <img src="{data_uri}" style="max-width:100%;max-height:380px;object-fit:contain;border-radius:4px;" alt="{nom}"/>
        </div>""", unsafe_allow_html=True)
    elif data_uri.strip().startswith("<svg"):
        svg_clean = re.sub(r'<rect[^>]*fill="#(?:1a0f05|0d0a07|111|000000|1f1f1f|0a0500)[^"]*"[^>]*/?>',
                           '', data_uri, flags=re.IGNORECASE)
        st.markdown(f"""<div style="border:2px solid #b8860b;border-radius:6px;padding:12px;
                    background:#f5ead0;display:flex;justify-content:center;max-width:320px;margin:0 auto;">{svg_clean}</div>""",
                    unsafe_allow_html=True)

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
                    invalidate_cache(); st.success("Illustration supprimée."); st.rerun()
        else:
            st.caption("Aucune illustration pour cet objet.")

        if is_admin and eq_id is not None:
            st.markdown("---")
            method = st.radio("Ajouter une illustration", ["🔗 Coller une URL", "📂 Upload fichier"],
                              horizontal=True, key=f"method_{key_prefix}_{eq_id}")
            if method == "🔗 Coller une URL":
                st.caption("Clic droit → Copier l'adresse de l'image → coller ici")
                url_input = st.text_input("URL de l'image", placeholder="https://...", key=f"url_{key_prefix}_{eq_id}")
                if url_input and url_input.startswith("http"):
                    try:
                        st.image(url_input, caption="Aperçu", width=250)
                        if st.button("✅ Valider cette image", key=f"save_url_{key_prefix}_{eq_id}"):
                            with st.spinner("Téléchargement..."):
                                b64 = telecharger_url_base64(url_input)
                            if b64:
                                execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s", (b64, int(eq_id)))
                                invalidate_cache(); st.success(f"Illustration de « {nom} » sauvegardée !"); st.rerun()
                            else:
                                st.error("Impossible de télécharger. Essayez d'uploader le fichier.")
                    except Exception:
                        st.warning("URL invalide ou image inaccessible.")
            else:
                uploaded = st.file_uploader("Glissez-déposez ou choisissez un fichier",
                                            type=["png","jpg","jpeg","webp","gif","svg"],
                                            key=f"upload_{key_prefix}_{eq_id}")
                if uploaded is not None:
                    st.image(uploaded, caption="Aperçu", width=250)
                    if st.button("✅ Valider cette image", key=f"save_img_{key_prefix}_{eq_id}"):
                        if uploaded.type == "image/svg+xml":
                            svg_text = uploaded.read().decode("utf-8", errors="ignore")
                            execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s", (svg_text, int(eq_id)))
                        else:
                            b64 = image_vers_base64(uploaded)
                            if b64:
                                execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s", (b64, int(eq_id)))
                        invalidate_cache(); st.success(f"Illustration de « {nom} » sauvegardée !"); st.rerun()
            st.markdown("")
            with st.expander("🎨 Générer un SVG avec Claude"):
                btn_lbl = "Regénérer le SVG" if has_img and stockee.strip().startswith("<svg") else "Générer un SVG"
                if st.button(btn_lbl, key=f"gen_svg_{key_prefix}_{eq_id}"):
                    with st.spinner(f"Génération SVG de « {nom} »..."):
                        nouveau_svg = generer_svg_arme(nom, sous_cat, notes, degats)
                    if nouveau_svg:
                        execute("UPDATE equipements SET svg_illustration=%s WHERE id=%s", (nouveau_svg, int(eq_id)))
                        invalidate_cache(); st.success("SVG sauvegardé !"); st.rerun()
                    else:
                        st.error("La génération a échoué.")

# ─────────────────────────────────────────────
#  HELPERS D'AFFICHAGE DU CATALOGUE
# ─────────────────────────────────────────────
def _cols_display_melee(df):
    base  = ["categorie","sous_categorie","nom","poids_kg","prix_deniers"]
    stats = [c for c in COLS_ARMES_COMMUNES if c in df.columns]
    cols  = [c for c in base + stats + ["notes"] if c in df.columns]
    rename = {"categorie":"Catégorie","sous_categorie":"Sous-catégorie","nom":"Nom",
              "poids_kg":"Enc.","prix_deniers":"Prix (deniers)","notes":"Notes",**LABELS_COMMUNES}
    return cols, rename

def _cols_display_tir(df):
    base  = ["categorie","sous_categorie","nom","poids_kg","prix_deniers"]
    stats = [c for c in COLS_ARMES_COMMUNES[:1] + COLS_ARMES_TIR if c in df.columns]
    cols  = [c for c in base + stats + ["notes"] if c in df.columns]
    rename = {"categorie":"Catégorie","sous_categorie":"Sous-catégorie","nom":"Nom",
              "poids_kg":"Enc.","prix_deniers":"Prix (deniers)","notes":"Notes",**LABELS_COMMUNES,**LABELS_TIR}
    return cols, rename

def _cols_display_lancer(df):
    base  = ["categorie","sous_categorie","nom","poids_kg","prix_deniers"]
    stats = [c for c in COLS_ARMES_COMMUNES + COLS_ARMES_LANCER if c in df.columns]
    cols  = [c for c in base + stats + ["notes"] if c in df.columns]
    rename = {"categorie":"Catégorie","sous_categorie":"Sous-catégorie","nom":"Nom",
              "poids_kg":"Enc.","prix_deniers":"Prix (deniers)","notes":"Notes",**LABELS_COMMUNES,**LABELS_LANCER}
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

    if "sous_categorie" in filtered.columns:
        mask_tir    = filtered["sous_categorie"].apply(is_tir)
        mask_lancer = filtered["sous_categorie"].apply(is_lancer)
        mask_arme   = filtered["sous_categorie"].apply(is_arme)
        df_melee  = filtered[~mask_tir & ~mask_lancer & mask_arme]
        df_tir    = filtered[mask_tir]
        df_lancer = filtered[mask_lancer]
        df_autres = filtered[~mask_arme]
    else:
        df_melee = filtered; df_tir = df_lancer = df_autres = pd.DataFrame()

    tab_melee, tab_tir, tab_lancer, tab_autres = st.tabs([
        f"⚔️ Armes de mêlée ({len(df_melee)})",
        f"🏹 Armes de tir ({len(df_tir)})",
        f"🎯 Armes de lancer ({len(df_lancer)})",
        f"🎒 Autres équipements ({len(df_autres)})",
    ])

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
                        afficher_illustration(rows_list[i+j], is_admin=is_admin, key_prefix=f"{tab_prefix}_{i+j}")

    with tab_melee:   _render_section(df_melee,  _cols_display_melee,  f"{key_prefix}_mel")
    with tab_tir:     _render_section(df_tir,    _cols_display_tir,    f"{key_prefix}_tir")
    with tab_lancer:  _render_section(df_lancer, _cols_display_lancer, f"{key_prefix}_lan")
    with tab_autres:
        if df_autres.empty:
            st.caption("Aucun équipement dans cette sélection.")
        else:
            cols_base = ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes"]
            cols_show = [c for c in cols_base if c in df_autres.columns]
            rename_base = {"categorie":"Catégorie","sous_categorie":"Sous-catégorie","nom":"Nom",
                           "poids_kg":"Enc.","prix_deniers":"Prix (deniers)","notes":"Notes"}
            st.dataframe(df_autres[cols_show].rename(columns=rename_base), use_container_width=True, hide_index=True)
            st.markdown("#### 🖼️ Illustrations")
            rows_list = [df_autres.iloc[i] for i in range(len(df_autres))]
            for i in range(0, len(rows_list), 3):
                grid_cols = st.columns(3)
                for j, col in enumerate(grid_cols):
                    if i + j < len(rows_list):
                        with col:
                            afficher_illustration(rows_list[i+j], is_admin=is_admin, key_prefix=f"{key_prefix}_aut_{i+j}")

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─────────────────────────────────────────────
#  PAGE : LOGIN
# ─────────────────────────────────────────────
def page_login():
    st.markdown("""<div class="banner"><h1>🐉 Rêve de Dragon</h1>
        <p>Gestion de l'équipement des aventuriers</p></div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### Identification")
        username = st.text_input("Nom d'aventurier", placeholder="Votre identifiant...")
        password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
        if st.button("🗝️  Entrer dans la taverne", use_container_width=True):
            user = login(username, password)
            if user:
                st.session_state.user = user; st.rerun()
            else:
                st.error("Identifiants incorrects. Le portier vous refuse l'entrée.")

# ─────────────────────────────────────────────
#  PAGE : ADMIN
# ─────────────────────────────────────────────
def page_admin():
    user = st.session_state.user
    st.markdown(f"""<div class="banner"><h1>🐉 Rêve de Dragon</h1>
        <p>Tableau du Maître des Rêves — {user['username']}</p></div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["⚔️ Catalogue","➕ Ajouter équipement","🎒 Inventaires joueurs","👤 Gestion joueurs"])

    with tab1:
        df = load_equipements()
        afficher_catalogue(df, key_prefix="admin_cat", is_admin=True)
        st.markdown("---")
        st.markdown("##### ✏️ Modifier les stats d'une arme")
        if not df.empty:
            to_edit = st.selectbox("Sélectionner l'arme à modifier", sorted(df["nom"].tolist()), key="admin_edit_sel")
            row_edit = df[df["nom"] == to_edit].iloc[0]
            eq_id_edit = int(row_edit["id"])
            sous_cat_edit = str(row_edit.get("sous_categorie",""))
            tir_mode    = is_tir(sous_cat_edit)
            lancer_mode = is_lancer(sous_cat_edit)
            with st.form(key="form_edit_arme"):
                st.markdown(f"**{to_edit}**")
                all_sous = TOUTES_SOUS_CATEGORIES.copy()
                if sous_cat_edit and sous_cat_edit not in all_sous:
                    all_sous = sorted(all_sous + [sous_cat_edit])
                sous_idx = all_sous.index(sous_cat_edit) if sous_cat_edit in all_sous else 0
                edit_sous_cat = st.selectbox("Sous-catégorie", all_sous, index=sous_idx)
                edit_notes = st.text_input("Notes", value=str(row_edit.get("notes") or ""))

                ce1, ce2, ce3 = st.columns(3)
                with ce1:
                    poids_actuel_enc = float(row_edit.get("poids_kg") or 0) * ENC_PAR_KG
                    edit_enc = st.number_input(
                        "Encombrement (enc.)",
                        min_value=0.0, step=0.5, format="%.1f",
                        value=poids_actuel_enc,
                        help="1 enc. = 2 kg. Saisissez directement en points d'encombrement."
                    )
                with ce2:
                    edit_prix = st.number_input(
                        "Prix (deniers)",
                        min_value=0, step=10,
                        value=int(row_edit.get("prix_deniers") or 0)
                    )
                with ce3:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    st.caption(f"Actuellement : **{poids_actuel_enc:.1f} enc.** ({float(row_edit.get('poids_kg') or 0):.2f} kg)")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    edit_degats = st.text_input("Dégâts", value=str(row_edit.get("degats") or ""))
                    edit_mains  = st.text_input("Mains",  value=str(row_edit.get("mains")  or ""))
                with c2:
                    edit_force = st.text_input("Force requise", value=str(row_edit.get("force_requise") or ""))
                    edit_res   = st.text_input("Résistance",    value=str(row_edit.get("resistance")    or ""))
                with c3:
                    if tir_mode or lancer_mode:
                        edit_m_dist = st.text_input("M. distance", value=str(row_edit.get("m_distance") or ""))
                        edit_portee = st.text_input("Portée max",  value=str(row_edit.get("portee_max") or ""))
                    else:
                        edit_m_dist = edit_portee = ""
                with c4:
                    if tir_mode:
                        edit_magasin  = st.text_input("Magasin",          value=str(row_edit.get("magasin")          or ""))
                        edit_tir_rech = st.text_input("Tir/Rechargement", value=str(row_edit.get("tir_rechargement") or ""))
                    else:
                        edit_magasin = edit_tir_rech = ""
                if st.form_submit_button("💾 Sauvegarder les stats"):
                    edit_poids_kg = edit_enc / ENC_PAR_KG
                    if tir_mode:
                        execute("""UPDATE equipements SET sous_categorie=%s, notes=%s, poids_kg=%s, prix_deniers=%s,
                                   degats=%s, mains=%s, force_requise=%s, resistance=%s,
                                   m_distance=%s, portee_max=%s, magasin=%s, tir_rechargement=%s WHERE id=%s""",
                                (edit_sous_cat, edit_notes or None, edit_poids_kg, edit_prix,
                                 edit_degats or None, edit_mains or None,
                                 edit_force or None, edit_res or None,
                                 edit_m_dist or None, edit_portee or None,
                                 edit_magasin or None, edit_tir_rech or None, eq_id_edit))
                    elif lancer_mode:
                        execute("""UPDATE equipements SET sous_categorie=%s, notes=%s, poids_kg=%s, prix_deniers=%s,
                                   degats=%s, mains=%s, force_requise=%s, resistance=%s,
                                   m_distance=%s, portee_max=%s WHERE id=%s""",
                                (edit_sous_cat, edit_notes or None, edit_poids_kg, edit_prix,
                                 edit_degats or None, edit_mains or None,
                                 edit_force or None, edit_res or None,
                                 edit_m_dist or None, edit_portee or None, eq_id_edit))
                    else:
                        execute("""UPDATE equipements SET sous_categorie=%s, notes=%s, poids_kg=%s, prix_deniers=%s,
                                   degats=%s, mains=%s, force_requise=%s, resistance=%s WHERE id=%s""",
                                (edit_sous_cat, edit_notes or None, edit_poids_kg, edit_prix,
                                 edit_degats or None, edit_mains or None,
                                 edit_force or None, edit_res or None, eq_id_edit))
                    invalidate_cache(); st.success(f"Stats de « {to_edit} » mises à jour."); st.rerun()

        st.markdown("---")
        st.markdown("##### 🗑️ Supprimer un équipement")
        if not df.empty:
            to_delete = st.selectbox("Sélectionner l'objet à supprimer", sorted(df["nom"].tolist()), key="admin_del")
            if st.button("Supprimer cet objet", type="primary"):
                obj_id = int(df[df["nom"] == to_delete]["id"].values[0])
                execute("DELETE FROM equipements WHERE id=%s", (obj_id,))
                invalidate_cache(); st.success(f"« {to_delete} » retiré du catalogue."); st.rerun()

    with tab2:
        st.markdown("#### Ajouter manuellement")
        c1, c2 = st.columns(2)
        with c1:
            new_cat   = st.text_input("Catégorie", value="Armes")
            new_sous  = st.selectbox("Sous-catégorie", TOUTES_SOUS_CATEGORIES, key="add_sous_cat")
            new_nom   = st.text_input("Nom de l'objet")
            new_notes = st.text_input("Notes (optionnel)")
        with c2:
            new_poids = st.number_input("Poids (kg)",     min_value=0.0, step=0.05, format="%.2f")
            new_prix  = st.number_input("Prix (deniers)", min_value=0,   step=10)
            new_degats= st.text_input("Dégâts (+dom)",    placeholder="ex: A+3")
            new_mains = st.text_input("Mains",            placeholder="ex: 1 ou 1\\2")
            new_force = st.text_input("Force requise",    placeholder="ex: 11")
            new_res   = st.text_input("Résistance",       placeholder="ex: 12")
        tir_mode_new    = is_tir(new_sous)
        lancer_mode_new = is_lancer(new_sous)
        if tir_mode_new:
            st.markdown("**Spécifique armes de tir**")
            c1t, c2t, c3t, c4t = st.columns(4)
            with c1t: new_m_dist  = st.text_input("M. distance")
            with c2t: new_portee  = st.text_input("Portée max")
            with c3t: new_magasin = st.text_input("Magasin")
            with c4t: new_tir_r   = st.text_input("Tir/Rechargement")
        elif lancer_mode_new:
            st.markdown("**Spécifique armes de lancer**")
            c1t, c2t = st.columns(2)
            with c1t: new_m_dist = st.text_input("M. distance")
            with c2t: new_portee = st.text_input("Portée max")
            new_magasin = new_tir_r = ""
        else:
            new_m_dist = new_portee = new_magasin = new_tir_r = ""
        if st.button("✅ Ajouter au catalogue"):
            if new_nom.strip():
                execute("""INSERT INTO equipements (categorie, sous_categorie, nom, poids_kg, prix_deniers, notes,
                           degats, mains, force_requise, resistance, m_distance, portee_max, magasin, tir_rechargement)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (new_cat.strip(), new_sous.strip(), new_nom.strip(), new_poids, new_prix, new_notes.strip(),
                         new_degats or None, new_mains or None, new_force or None, new_res or None,
                         new_m_dist or None, new_portee or None, new_magasin or None, new_tir_r or None))
                invalidate_cache(); st.success(f"« {new_nom} » ajouté !"); st.rerun()
            else:
                st.warning("Le nom de l'objet est obligatoire.")

        st.markdown("---")
        st.markdown("#### Importer un fichier CSV ou Excel")
        uploaded = st.file_uploader("Choisir un fichier CSV ou Excel", type=["csv","xlsx","xls"])
        if uploaded:
            try:
                col_map = {"Catégorie":"categorie","Sous-catégorie":"sous_categorie","Nom":"nom",
                           "Poids (Kg)":"poids_kg","Prix (Deniers)":"prix_deniers","Notes":"notes",
                           "Dégâts":"degats","Mains":"mains","Force requise":"force_requise",
                           "Résistance":"resistance","M. distance":"m_distance","Portée max":"portee_max",
                           "Magasin":"magasin","Tir/Rechargement":"tir_rechargement"}
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
                        st.warning(f"Onglet « {sheet_name} » ignoré."); continue
                    df_sheet = df_sheet.dropna(subset=["nom"])
                    df_sheet["_onglet"] = sheet_name
                    frames.append(df_sheet)
                if not frames:
                    st.error("Aucun onglet valide.")
                else:
                    df_import = pd.concat(frames, ignore_index=True)
                    if "poids_kg" in df_import.columns:
                        df_import["poids_kg"] = df_import["poids_kg"].astype(str).str.replace(",",".").pipe(pd.to_numeric,errors="coerce").fillna(0.0)
                    else:
                        df_import["poids_kg"] = 0.0
                    if "prix_deniers" in df_import.columns:
                        df_import["prix_deniers"] = pd.to_numeric(df_import["prix_deniers"],errors="coerce").fillna(0).astype(int)
                    else:
                        df_import["prix_deniers"] = 0
                    for col in ["notes","degats","mains","force_requise","resistance","m_distance","portee_max","magasin","tir_rechargement"]:
                        if col in df_import.columns:
                            df_import[col] = df_import[col].fillna("").astype(str).str.strip().replace("", None)
                        else:
                            df_import[col] = None
                    if "categorie"     not in df_import.columns: df_import["categorie"]     = df_import["_onglet"]
                    if "sous_categorie" not in df_import.columns: df_import["sous_categorie"] = ""
                    df_import = df_import.drop(columns=["_onglet"], errors="ignore")
                    st.markdown(f"**{len(df_import)} objets détectés**")
                    st.dataframe(df_import.head(15), use_container_width=True)
                    all_cols = ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes",
                                "degats","mains","force_requise","resistance","m_distance","portee_max","magasin","tir_rechargement"]
                    keep = [c for c in all_cols if c in df_import.columns]
                    if st.button("📥 Importer dans la base"):
                        records = [tuple(r[c] for c in keep) for _,r in df_import.iterrows()]
                        executemany(f"INSERT INTO equipements ({','.join(keep)}) VALUES ({','.join(['%s']*len(keep))})", records)
                        invalidate_cache(); st.success(f"✅ {len(records)} objets importés !"); st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

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
                    new_poids_max_j = st.number_input("Enc. max sur soi", min_value=0.0,
                                                       value=poids_max_j * 0.5, step=0.5, format="%.1f", key="admin_poids_max")
                if st.button("💾 Sauvegarder les paramètres", key="admin_save_params"):
                    execute("UPDATE users SET monture=%s, poids_max_joueur=%s WHERE id=%s",
                            (new_monture_j, new_poids_max_j * 2, player_id))
                    invalidate_cache(); st.success(f"Paramètres de {selected_player} mis à jour."); st.rerun()

            df_inv = load_inventory(player_id)
            if df_inv.empty:
                st.info(f"{selected_player} ne possède aucun objet.")
            else:
                df_inv["poids_total"] = df_inv["poids_kg"] * df_inv["quantite"]
                df_soi  = df_inv[df_inv["localisation"] == "soi"]
                df_mont = df_inv[df_inv["localisation"] == "monture"]
                poids_soi  = float(df_soi["poids_total"].sum())
                poids_mont = float(df_mont["poids_total"].sum())
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""<div class="metric-card"><div class="metric-value">{len(df_inv)}</div>
                        <div class="metric-label">Objets différents</div></div>""", unsafe_allow_html=True)
                with c2:
                    couleur = "#c0392b" if poids_max_j > 0 and poids_soi > poids_max_j else "#b8860b"
                    enc_soi_lbl = enc(poids_soi)
                    enc_max_lbl = enc(poids_max_j)
                    st.markdown(f"""<div class="metric-card">
                        <div class="metric-value" style="color:{couleur}">{enc_soi_lbl} enc.</div>
                        <div class="metric-label">Sur soi{f" / {enc_max_lbl} max" if poids_max_j > 0 else ""}</div>
                        </div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class="metric-card"><div class="metric-value">{enc(poids_mont)} enc.</div>
                        <div class="metric-label">Sur {monture_j if monture_j != "Aucune" else "monture"}</div>
                        </div>""", unsafe_allow_html=True)
                st.markdown("")

                def _afficher_inventaire_section(df_section, label_icon):
                    for cat in sorted(df_section["categorie"].dropna().unique()):
                        df_c = df_section[df_section["categorie"] == cat].copy()
                        df_c["poids_total"] = df_c["poids_kg"] * df_c["quantite"]
                        mask_tir    = df_c["sous_categorie"].apply(is_tir)
                        mask_lancer = df_c["sous_categorie"].apply(is_lancer)
                        with st.expander(f"{label_icon} {cat}  •  {enc(float(df_c['poids_total'].sum()))} enc.", expanded=False):
                            for df_sub, fn, lbl in [
                                (df_c[~mask_tir & ~mask_lancer], _cols_display_melee, "*Mêlée*"),
                                (df_c[mask_tir],                 _cols_display_tir,   "*Tir*"),
                                (df_c[mask_lancer],              _cols_display_lancer, "*Lancer*"),
                            ]:
                                if not df_sub.empty:
                                    st.markdown(lbl)
                                    cols_, ren_ = fn(df_sub)
                                    extra = ["quantite","poids_total","localisation"]
                                    # poids_kg exclu : on affiche poids_total à la place (même label "Enc." sinon doublon)
                                    exclude = {"poids_kg"}
                                    seen = set()
                                    show = []
                                    for col_ in extra + cols_:
                                        if col_ in df_sub.columns and col_ not in seen and col_ not in exclude:
                                            show.append(col_)
                                            seen.add(col_)
                                    ren_.update({"quantite":"Qté","poids_total":"Enc.","localisation":"Lieu"})
                                    # S'assurer qu'aucun label cible n'est en doublon après rename
                                    labels_vus = set()
                                    show_final = []
                                    for col_ in show:
                                        label = ren_.get(col_, col_)
                                        if label not in labels_vus:
                                            show_final.append(col_)
                                            labels_vus.add(label)
                                    st.dataframe(df_sub[show_final].rename(columns=ren_), use_container_width=True, hide_index=True)

                st.markdown("**🧍 Sur soi**")
                if df_soi.empty: st.caption("Aucun objet sur soi.")
                else: _afficher_inventaire_section(df_soi, "⚔️")
                if monture_j != "Aucune":
                    st.markdown(f"**🐴 Sur la {monture_j}**")
                    if df_mont.empty: st.caption(f"Aucun objet sur la {monture_j}.")
                    else: _afficher_inventaire_section(df_mont, "🐴")

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
                            invalidate_cache(); st.rerun()
                with c2:
                    st.markdown("##### 🗑️ Retirer un objet de l'inventaire")
                    to_remove = st.selectbox("Objet à retirer", df_inv["nom"].tolist(), key="admin_remove")
                    if st.button("🗑️ Retirer", key="admin_remove_btn"):
                        inv_id = int(df_inv[df_inv["nom"] == to_remove]["inv_id"].values[0])
                        execute("DELETE FROM inventaire WHERE id=%s", (inv_id,))
                        invalidate_cache(); st.success(f"« {to_remove} » retiré."); st.rerun()

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
                    loc_opts = ["soi"] + (["monture"] if monture_cur != "Aucune" else [])
                    loc_lbls = ["🧍 Sur soi"] + ([f"🐴 Sur la {monture_cur}"] if monture_cur != "Aucune" else [])
                    loc_ch   = st.selectbox("Ranger où ?", loc_lbls, key="admin_add_loc")
                    loc_v    = loc_opts[loc_lbls.index(loc_ch)]
                if st.button("➕ Ajouter à l'inventaire"):
                    eq_id = int(df_eq[df_eq["nom"] == chosen_eq]["id"].values[0])
                    execute("INSERT INTO inventaire (player_id, equipement_id, quantite, localisation) VALUES (%s,%s,%s,%s)",
                            (player_id, eq_id, qty, loc_v))
                    invalidate_cache(); st.success(f"« {chosen_eq} » (x{qty}) ajouté — {loc_ch}."); st.rerun()

    with tab4:
        st.markdown("#### Créer un compte joueur")
        c1, c2 = st.columns(2)
        with c1: new_username = st.text_input("Nom d'utilisateur", key="new_user")
        with c2: new_password = st.text_input("Mot de passe", type="password", key="new_pass")
        if st.button("👤 Créer le compte"):
            if new_username.strip() and new_password.strip():
                try:
                    execute("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'joueur')",
                            (new_username.strip(), hash_password(new_password)))
                    invalidate_cache(); st.success(f"Compte « {new_username} » créé.")
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
                with c1: st.markdown(f"🧙 **{p['username']}**")
                with c2:
                    if st.button("Supprimer", key=f"del_{p['id']}"):
                        execute("DELETE FROM users WHERE id=%s", (p["id"],))
                        invalidate_cache(); st.rerun()
        else:
            st.info("Aucun joueur enregistré.")

# ─────────────────────────────────────────────
#  CONTENEURS
# ─────────────────────────────────────────────
CONTENEURS_SOI = ["Porté sur soi", "Sac à dos", "Ceinturon", "Bourse", "Outre / Gourde", "Etui"]
CONTENEURS_MONTURE = ["Monture"]

CONTENEUR_ICONE = {
    "Porté sur soi":   "🧍",
    "Sac à dos":       "🎒",
    "Ceinturon":       "👜",
    "Bourse":          "💰",
    "Outre / Gourde":  "🫙",
    "Etui":            "📦",
    "Monture":         "🐴",
}

ICONES_DISPO = ["🗃️","🎒","💼","👝","🧳","📫","🪣","🧺","🛒","⚗️","🗡️","🏹","🪬","📿","🧲","🪤","🎣","🛡️","🔮","📜"]

def conteneur_to_localisation(conteneur: str) -> str:
    return "monture" if conteneur in CONTENEURS_MONTURE else "soi"

@st.cache_data(ttl=30)
def load_conteneurs_joueur(player_id: int) -> list:
    rows = query(
        "SELECT id, nom, icone FROM conteneurs_joueur WHERE player_id=%s ORDER BY id",
        (player_id,)
    )
    return [dict(r) for r in rows] if rows else []

@st.cache_data(ttl=30)
def load_inventory_v2(player_id: int) -> pd.DataFrame:
    rows = query("""
        SELECT i.id AS inv_id, i.quantite, i.localisation,
               COALESCE(i.conteneur, 'Porté sur soi') AS conteneur,
               e.id AS eq_id, e.nom, e.categorie, e.sous_categorie,
               e.poids_kg, e.prix_deniers, e.notes,
               e.degats, e.mains, e.force_requise, e.resistance,
               e.m_distance, e.portee_max, e.magasin, e.tir_rechargement
        FROM inventaire i
        JOIN equipements e ON e.id = i.equipement_id
        WHERE i.player_id = %s
        ORDER BY i.conteneur, e.categorie, e.nom
    """, (player_id,))
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    return _appliquer_canon(df)

def invalidate_cache_v2():
    invalidate_cache()
    load_inventory_v2.clear()
    load_conteneurs_joueur.clear()

# ─────────────────────────────────────────────
#  PAGE : JOUEUR
# ─────────────────────────────────────────────
def page_joueur():
    user = st.session_state.user

    st.markdown("""
    <style>
    .fiche-wrapper {
        background: #f5ead0;
        border: 2px solid #b8860b;
        border-radius: 6px;
        padding: 1.2rem 1.5rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 18px rgba(0,0,0,0.35);
    }
    .fiche-titre-perso {
        font-family: 'Cinzel', serif;
        font-size: 2rem;
        color: #2c1a0e;
        border-bottom: 2px solid #b8860b;
        margin-bottom: 0.8rem;
        padding-bottom: 0.3rem;
        letter-spacing: 0.06em;
    }
    .fiche-sous-titre {
        font-family: 'Cinzel', serif;
        font-size: 0.65rem;
        color: #5c3a1e;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }
    .conteneur-box {
        background: rgba(245,234,208,0.6);
        border: 1px solid #b8860b;
        border-radius: 4px;
        padding: 0.6rem 0.8rem 0.8rem;
        margin-bottom: 0.8rem;
        min-height: 80px;
    }
    .conteneur-header {
        font-family: 'Cinzel', serif;
        font-size: 0.75rem;
        color: #2c1a0e;
        font-weight: 700;
        letter-spacing: 0.08em;
        border-bottom: 1px solid #b8860b;
        margin-bottom: 0.5rem;
        padding-bottom: 0.2rem;
        display: flex;
        justify-content: space-between;
    }
    .conteneur-poids {
        font-family: 'Crimson Text', serif;
        font-size: 0.75rem;
        color: #8b1a1a;
        font-style: italic;
    }
    .item-ligne {
        font-family: 'Crimson Text', serif;
        font-size: 0.82rem;
        color: #2c1a0e;
        border-bottom: 1px solid #d9cdb0;
        padding: 2px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .item-nom { flex: 1; }
    .item-poids {
        font-size: 0.72rem;
        color: #5c3a1e;
        margin-left: 8px;
        white-space: nowrap;
    }
    .item-stat {
        font-size: 0.70rem;
        color: #8b1a1a;
        margin-left: 6px;
        font-style: italic;
        white-space: nowrap;
    }
    .fiche-total {
        font-family: 'Cinzel', serif;
        font-size: 1rem;
        color: #2c1a0e;
        text-align: right;
        border-top: 2px solid #b8860b;
        padding-top: 0.4rem;
        margin-top: 0.5rem;
    }
    .fiche-total span { color: #b8860b; font-size: 1.2rem; }
    .poids-alert { color: #8b1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""<div class="banner"><h1>🐉 Rêve de Dragon</h1>
        <p>Carnet d'aventurier de <em>{user['username']}</em></p></div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📜 Ma fiche", "⚔️ Catalogue", "🗃️ Mes conteneurs"])

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
                new_poids_max = st.number_input("Enc. max sur soi", min_value=0.0,
                                                 value=poids_max * 0.5, step=0.5, format="%.1f", key="j_poids_max")
            if st.button("💾 Sauvegarder", key="j_save_params"):
                execute("UPDATE users SET monture=%s, poids_max_joueur=%s WHERE id=%s",
                        (new_monture, new_poids_max * 2, user["id"]))
                invalidate_cache_v2(); st.success("Paramètres sauvegardés !"); st.rerun()

        conteneurs_perso = load_conteneurs_joueur(user["id"])
        noms_perso  = [cp["nom"]   for cp in conteneurs_perso]
        icones_perso = {cp["nom"]: cp["icone"] for cp in conteneurs_perso}
        ids_perso    = {cp["nom"]: cp["id"]    for cp in conteneurs_perso}

        conteneurs_dispos = CONTENEURS_SOI.copy()
        if monture_actuelle != "Aucune":
            conteneurs_dispos += CONTENEURS_MONTURE
        conteneurs_dispos += noms_perso

        icones_all = {**CONTENEUR_ICONE, **icones_perso}

        df_inv = load_inventory_v2(user["id"])

        if df_inv.empty:
            st.info("Votre besace est vide. Consultez le catalogue pour vous équiper.")
        else:
            df_inv = df_inv.copy()
            df_inv["poids_total"] = df_inv["poids_kg"] * df_inv["quantite"]

            mask_soi    = df_inv["conteneur"].apply(lambda x: conteneur_to_localisation(x) == "soi")
            poids_soi   = float(df_inv[mask_soi]["poids_total"].sum())
            poids_mont  = float(df_inv[~mask_soi]["poids_total"].sum())
            poids_total = float(df_inv["poids_total"].sum())

            col_pdf, col_info = st.columns([1, 3])
            with col_pdf:
                pdf_bytes = generer_fiche_pdf(
                    nom_perso=user["username"],
                    df_inv=df_inv,
                    monture=monture_actuelle,
                    poids_max=poids_max,
                )
                st.download_button(
                    label="📜 Télécharger ma fiche PDF",
                    data=pdf_bytes,
                    file_name=f"fiche_{user['username']}.pdf",
                    mime="application/pdf",
                    key="dl_fiche_pdf",
                )
            with col_info:
                couleur_soi = "poids-alert" if poids_max > 0 and poids_soi > poids_max else ""
                st.markdown(
                    f"<span class='{couleur_soi}' style='color:#2c1a0e;font-family:Crimson Text,serif;font-size:0.9rem;'>"
                    f"Sur soi : <b>{enc(poids_soi)} enc.</b>"
                    + (f" / {enc(poids_max)} max" if poids_max > 0 else "")
                    + (f" &nbsp;|&nbsp; {monture_actuelle} : <b>{enc(poids_mont)} enc.</b>" if monture_actuelle != "Aucune" else "")
                    + f" &nbsp;|&nbsp; Total : <b>{enc(poids_total)} enc.</b></span>",
                    unsafe_allow_html=True
                )
            st.markdown("")

            def _html_items(df_c: pd.DataFrame) -> str:
                if df_c.empty:
                    return "<div style='color:#a09070;font-style:italic;font-size:0.78rem;padding:4px 0;'>— vide —</div>"
                parts = []
                for _, row in df_c.iterrows():
                    nom     = str(row.get("nom", ""))
                    qty     = int(row.get("quantite", 1))
                    poids   = float(row.get("poids_total", 0) or 0)
                    degats  = str(row.get("degats", "") or "")
                    label   = (nom + " ×" + str(qty)) if qty > 1 else nom
                    stat_html  = ("<span class='item-stat'>" + degats + "</span>") if degats else ""
                    poids_html = ("<span class='item-poids'>" + enc(poids) + " enc.</span>") if poids > 0 else ""
                    parts.append(
                        "<div class='item-ligne'>"
                        "<span class='item-nom'>" + label + "</span>"
                        + stat_html + poids_html +
                        "</div>"
                    )
                return "".join(parts)

            def _conteneur_html(nom_cont: str, df_c: pd.DataFrame, icone: str = "📦") -> str:
                poids   = float(df_c["poids_total"].sum()) if not df_c.empty else 0.0
                poids_s = enc(poids) + " enc." if poids > 0 else "vide"
                return (
                    "<div class='conteneur-box'>"
                    "<div class='conteneur-header'>"
                    "<span>" + icone + " " + nom_cont + "</span>"
                    "<span class='conteneur-poids'>" + poids_s + "</span>"
                    "</div>"
                    + _html_items(df_c) +
                    "</div>"
                )

            col_a_items = ["Porté sur soi", "Sac à dos"]
            col_b_items = ["Ceinturon", "Bourse", "Outre / Gourde", "Etui"]

            html_a = html_b = html_c = ""

            for cont in col_a_items:
                df_c = df_inv[df_inv["conteneur"] == cont]
                html_a += _conteneur_html(cont, df_c, icones_all.get(cont, "📦"))

            for cont in col_b_items:
                df_c = df_inv[df_inv["conteneur"] == cont]
                html_b += _conteneur_html(cont, df_c, icones_all.get(cont, "📦"))

            df_armes   = df_inv[df_inv["sous_categorie"].apply(is_arme)]
            df_armures = df_inv[df_inv["categorie"].str.lower().str.contains("armure", na=False)]
            poids_armes   = float(df_armes["poids_total"].sum())
            poids_armures = float(df_armures["poids_total"].sum())

            html_c += (
                "<div class='conteneur-box'>"
                "<div class='conteneur-header'>"
                "<span>⚔️ Armes</span>"
                "<span class='conteneur-poids'>+dom  rés. | " + enc(poids_armes) + " enc.</span>"
                "</div>"
                + _html_items(df_armes) +
                "</div>"
            )

            html_c += (
                "<div class='conteneur-box'>"
                "<div class='conteneur-header'>"
                "<span>🛡️ Armures</span>"
                "<span class='conteneur-poids'>prot. déter. | " + enc(poids_armures) + " enc.</span>"
                "</div>"
                + _html_items(df_armures) +
                "</div>"
            )

            if monture_actuelle != "Aucune":
                df_c = df_inv[df_inv["conteneur"] == "Monture"]
                html_c += _conteneur_html("Monture", df_c, "🐴")

            for idx, nom_cp in enumerate(noms_perso):
                df_c  = df_inv[df_inv["conteneur"] == nom_cp]
                icone = icones_perso.get(nom_cp, "🗃️")
                bloc  = _conteneur_html(nom_cp, df_c, icone)
                if idx % 3 == 0:   html_a += bloc
                elif idx % 3 == 1: html_b += bloc
                else:              html_c += bloc

            alert_cls = "poids-alert" if poids_max > 0 and poids_soi > poids_max else ""
            total_html = (
                "<div class='fiche-total " + alert_cls + "'>"
                "Enc. total &nbsp; <span>" + enc(poids_total) + "</span>"
                "</div>"
            )

            nom_perso_html = user["username"]
            fiche_html = (
                "<div class='fiche-wrapper'>"
                "<div class='fiche-titre-perso'>" + nom_perso_html + "</div>"
                "<div class='fiche-sous-titre'>Fiche d&rsquo;équipement — Rêve de Dragon</div>"
                "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;'>"
                "<div>" + html_a + "</div>"
                "<div>" + html_b + "</div>"
                "<div>" + html_c + "</div>"
                "</div>"
                + total_html +
                "</div>"
            )
            st.markdown(fiche_html, unsafe_allow_html=True)

        if not df_inv.empty:
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 🔀 Changer de conteneur")
                obj_move    = st.selectbox("Objet", df_inv["nom"].tolist(), key="j_move")
                row_move    = df_inv[df_inv["nom"] == obj_move].iloc[0]
                cont_actuel = row_move["conteneur"]
                autres_cont = [c for c in conteneurs_dispos if c != cont_actuel]
                nouveau_cont = st.selectbox(
                    f"Actuellement : {icones_all.get(cont_actuel,'')} {cont_actuel}  →  Vers",
                    autres_cont, key="j_move_dest"
                )
                if st.button("➡️ Déplacer", key="j_move_btn"):
                    inv_id  = int(row_move["inv_id"])
                    new_loc = conteneur_to_localisation(nouveau_cont)
                    execute("UPDATE inventaire SET conteneur=%s, localisation=%s WHERE id=%s",
                            (nouveau_cont, new_loc, inv_id))
                    invalidate_cache_v2(); st.rerun()
            with c2:
                st.markdown("##### 🗑️ Retirer un objet")
                to_remove = st.selectbox("Objet à retirer", df_inv["nom"].tolist(), key="j_remove")
                if st.button("🗑️ Retirer de mon inventaire", key="j_remove_btn"):
                    inv_id = int(df_inv[df_inv["nom"] == to_remove]["inv_id"].values[0])
                    execute("DELETE FROM inventaire WHERE id=%s", (inv_id,))
                    invalidate_cache_v2(); st.success(f"« {to_remove} » retiré."); st.rerun()

    with tab2:
        df = load_equipements()
        afficher_catalogue(df, key_prefix="joueur_cat")
        st.markdown("---")
        st.markdown("##### Ajouter un objet à mon inventaire")
        if not df.empty:
            conts_perso2 = [cp["nom"] for cp in load_conteneurs_joueur(user["id"])]
            pinfo2       = load_player_info(user["id"])
            monture2     = pinfo2.get("monture") or "Aucune"
            conts_dispos2 = CONTENEURS_SOI + (CONTENEURS_MONTURE if monture2 != "Aucune" else []) + conts_perso2

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                eq_list   = sorted(df["nom"].tolist())
                chosen_eq = st.selectbox("Choisir l'objet", eq_list, key="jadd_eq")
            with c2:
                qty = st.number_input("Quantité", min_value=1, max_value=99, value=1, key="jadd_qty")
            with c3:
                chosen_cont = st.selectbox("Ranger dans", conts_dispos2, key="jadd_cont")
            with c4:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("➕ Ajouter à mon inventaire", key="jadd_btn"):
                    eq_id = int(df[df["nom"] == chosen_eq]["id"].values[0])
                    loc_v = conteneur_to_localisation(chosen_cont)
                    execute(
                        "INSERT INTO inventaire (player_id, equipement_id, quantite, localisation, conteneur) VALUES (%s,%s,%s,%s,%s)",
                        (user["id"], eq_id, qty, loc_v, chosen_cont)
                    )
                    invalidate_cache_v2()
                    icone_ch = icones_all.get(chosen_cont, "🗃️")
                    st.success(f"« {chosen_eq} » (×{qty}) → {icone_ch} {chosen_cont} !")
                    st.rerun()

    with tab3:
        st.markdown("#### 🗃️ Mes conteneurs personnalisés")
        st.caption("Créez vos propres sections de rangement : sacoche de selle, boîte à alchimie, étui à cartes…")

        conteneurs_perso3 = load_conteneurs_joueur(user["id"])

        with st.form("form_nouveau_conteneur", clear_on_submit=True):
            st.markdown("##### ➕ Nouveau conteneur")
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                nouveau_nom = st.text_input("Nom du conteneur", placeholder="ex: Besace de selle, Coffret à herbes…")
            with c2:
                icone_choisie = st.selectbox("Icône", ICONES_DISPO)
            with c3:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                submitted = st.form_submit_button("✅ Créer")
            if submitted:
                if nouveau_nom.strip():
                    try:
                        execute(
                            "INSERT INTO conteneurs_joueur (player_id, nom, icone) VALUES (%s, %s, %s)",
                            (user["id"], nouveau_nom.strip(), icone_choisie)
                        )
                        invalidate_cache_v2()
                        st.success(f"{icone_choisie} « {nouveau_nom} » créé !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Le nom est obligatoire.")

        st.markdown("---")

        if not conteneurs_perso3:
            st.info("Vous n'avez pas encore de conteneur personnalisé.")
        else:
            st.markdown("##### Conteneurs existants")
            df_inv3 = load_inventory_v2(user["id"])
            for cp in conteneurs_perso3:
                nb_items = 0
                if not df_inv3.empty:
                    nb_items = len(df_inv3[df_inv3["conteneur"] == cp["nom"]])
                c1, c2, c3 = st.columns([1, 4, 1])
                with c1:
                    st.markdown(f"<span style='font-size:1.8rem'>{cp['icone']}</span>", unsafe_allow_html=True)
                with c2:
                    st.markdown(
                        f"**{cp['nom']}**  "
                        f"<span style='color:#5c3a1e;font-size:0.8rem;'>({nb_items} objet(s))</span>",
                        unsafe_allow_html=True
                    )
                with c3:
                    if st.button("🗑️ Supprimer", key=f"del_cont_{cp['id']}"):
                        if nb_items > 0:
                            execute(
                                "UPDATE inventaire SET conteneur='Porté sur soi', localisation='soi' WHERE player_id=%s AND conteneur=%s",
                                (user["id"], cp["nom"])
                            )
                        execute("DELETE FROM conteneurs_joueur WHERE id=%s AND player_id=%s",
                                (cp["id"], user["id"]))
                        invalidate_cache_v2()
                        st.success(f"Conteneur « {cp['nom']} » supprimé. Les objets ont été remis dans « Porté sur soi ».")
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
            st.session_state.user = None; st.rerun()

# ─────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────
if st.session_state.user is None:
    page_login()
elif st.session_state.user["role"] == "admin":
    page_admin()
else:
    page_joueur()
