import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from contextlib import contextmanager

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
/* Force la couleur du texte saisi dans TOUS les états */
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
/* Surcharge agressive des classes Streamlit internes */
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
/* Placeholder en gris clair */
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
#  CONNEXION NEON
# ─────────────────────────────────────────────
@contextmanager
def get_conn():
    """Ouvre une connexion PostgreSQL (Neon) et la ferme proprement."""
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
    rows = query("SELECT * FROM equipements ORDER BY categorie, sous_categorie, nom")
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

@st.cache_data(ttl=30)
def load_inventory(player_id: int) -> pd.DataFrame:
    rows = query("""
        SELECT i.id AS inv_id, i.quantite, i.localisation,
               e.id AS eq_id, e.nom, e.categorie, e.sous_categorie,
               e.poids_kg, e.prix_deniers, e.notes
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
        if df.empty:
            st.info("Le catalogue est vide. Importez des équipements.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                cats = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
                cat_filter = st.selectbox("Catégorie", cats)
            with c2:
                sub_df = df[df["categorie"] == cat_filter] if cat_filter != "Toutes" else df
                sous = ["Toutes"] + sorted(sub_df["sous_categorie"].dropna().unique().tolist())
                sous_filter = st.selectbox("Sous-catégorie", sous)
            with c3:
                search = st.text_input("🔍 Rechercher", placeholder="Nom de l'objet...")

            filtered = df.copy()
            if cat_filter  != "Toutes": filtered = filtered[filtered["categorie"]      == cat_filter]
            if sous_filter != "Toutes": filtered = filtered[filtered["sous_categorie"] == sous_filter]
            if search:                  filtered = filtered[filtered["nom"].str.contains(search, case=False, na=False)]

            st.markdown(f"**{len(filtered)}** objets trouvés")
            disp = ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes"]
            disp = [c for c in disp if c in filtered.columns]
            st.dataframe(
                filtered[disp].rename(columns={
                    "categorie":"Catégorie","sous_categorie":"Sous-catégorie",
                    "nom":"Nom","poids_kg":"Poids (kg)","prix_deniers":"Prix (deniers)","notes":"Notes"
                }),
                use_container_width=True, hide_index=True
            )

            st.markdown("---")
            st.markdown("##### 🗑️ Supprimer un équipement")
            to_delete = st.selectbox("Sélectionner l'objet à supprimer", sorted(df["nom"].tolist()))
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
        with c2:
            new_poids = st.number_input("Poids (kg)", min_value=0.0, step=0.05, format="%.2f")
            new_prix  = st.number_input("Prix (deniers)", min_value=0, step=10)
            new_notes = st.text_input("Notes (optionnel)")

        if st.button("✅ Ajouter au catalogue"):
            if new_nom.strip():
                execute("""
                    INSERT INTO equipements (categorie, sous_categorie, nom, poids_kg, prix_deniers, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (new_cat.strip(), new_sous.strip(), new_nom.strip(), new_poids, new_prix, new_notes.strip()))
                invalidate_cache()
                st.success(f"« {new_nom} » ajouté au catalogue !")
                st.rerun()
            else:
                st.warning("Le nom de l'objet est obligatoire.")

        st.markdown("---")
        st.markdown("#### Importer un fichier CSV ou Excel")
        st.caption("Format attendu : Catégorie;Sous-catégorie;Nom;Poids (Kg);Prix (Deniers);Notes — tous les onglets seront importés")
        uploaded = st.file_uploader("Choisir un fichier CSV ou Excel", type=["csv", "xlsx", "xls"])
        if uploaded:
            try:
                col_map = {
                    "Catégorie":"categorie","Sous-catégorie":"sous_categorie",
                    "Nom":"nom","Poids (Kg)":"poids_kg","Prix (Deniers)":"prix_deniers","Notes":"notes",
                }

                # ── Lire toutes les feuilles / le CSV ──
                import io
                filename = uploaded.name.lower()
                if filename.endswith(".csv"):
                    sheets = {"Feuille 1": pd.read_csv(uploaded, sep=";", encoding="latin-1")}
                else:
                    # calamine est un moteur Rust ultra-robuste qui ignore les styles
                    file_bytes = uploaded.read()
                    xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="calamine")
                    sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

                frames = []
                for sheet_name, df_sheet in sheets.items():
                    df_sheet = df_sheet.rename(columns=col_map)
                    # Garder uniquement les colonnes connues
                    keep_cols = [c for c in ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes"] if c in df_sheet.columns]
                    if "nom" not in keep_cols:
                        st.warning(f"Onglet « {sheet_name} » ignoré (colonne 'Nom' introuvable).")
                        continue
                    df_sheet = df_sheet[keep_cols].dropna(subset=["nom"])
                    df_sheet["_onglet"] = sheet_name
                    frames.append(df_sheet)

                if not frames:
                    st.error("Aucun onglet valide trouvé dans le fichier.")
                else:
                    df_import = pd.concat(frames, ignore_index=True)

                    if "poids_kg" in df_import.columns:
                        df_import["poids_kg"] = df_import["poids_kg"].astype(str).str.replace(",",".").astype(float)
                    else:
                        df_import["poids_kg"] = 0.0
                    if "prix_deniers" in df_import.columns:
                        df_import["prix_deniers"] = pd.to_numeric(df_import["prix_deniers"], errors="coerce").fillna(0).astype(int)
                    else:
                        df_import["prix_deniers"] = 0
                    if "notes" in df_import.columns:
                        df_import["notes"] = df_import["notes"].fillna("").astype(str)
                    else:
                        df_import["notes"] = ""
                    if "categorie" not in df_import.columns:
                        df_import["categorie"] = df_import["_onglet"]
                    if "sous_categorie" not in df_import.columns:
                        df_import["sous_categorie"] = ""

                    df_import = df_import.drop(columns=["_onglet"])

                    # Aperçu par onglet
                    st.markdown(f"**{len(df_import)} objets détectés** dans {len(frames)} onglet(s)")
                    st.dataframe(df_import.head(15), use_container_width=True)

                    keep = ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes"]
                    keep = [c for c in keep if c in df_import.columns]

                    if st.button("📥 Importer tous les onglets dans la base"):
                        records = [tuple(r[c] for c in keep) for _, r in df_import.iterrows()]
                        cols_sql = ", ".join(keep)
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

            # ── Paramètres du joueur (monture + poids max) ──
            pinfo = load_player_info(player_id)
            monture_j = pinfo.get("monture") or "Aucune"
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
                df_soi     = df_inv[df_inv["localisation"] == "soi"]
                df_mont    = df_inv[df_inv["localisation"] == "monture"]
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

                # Affichage sur soi
                st.markdown("**🧍 Sur soi**")
                if df_soi.empty:
                    st.caption("Aucun objet sur soi.")
                else:
                    for cat in sorted(df_soi["categorie"].dropna().unique()):
                        df_c = df_soi[df_soi["categorie"] == cat]
                        with st.expander(f"⚔️ {cat}  •  {df_c['poids_total'].sum():.2f} kg", expanded=False):
                            st.dataframe(df_c[["nom","quantite","poids_kg","poids_total","localisation"]].rename(columns={
                                "nom":"Objet","quantite":"Qté","poids_kg":"Poids unit.","poids_total":"Poids total","localisation":"Lieu"
                            }), use_container_width=True, hide_index=True)

                # Affichage sur monture
                if monture_j != "Aucune":
                    st.markdown(f"**🐴 Sur la {monture_j}**")
                    if df_mont.empty:
                        st.caption(f"Aucun objet sur la {monture_j}.")
                    else:
                        for cat in sorted(df_mont["categorie"].dropna().unique()):
                            df_c = df_mont[df_mont["categorie"] == cat]
                            with st.expander(f"⚔️ {cat}  •  {df_c['poids_total'].sum():.2f} kg", expanded=False):
                                st.dataframe(df_c[["nom","quantite","poids_kg","poids_total"]].rename(columns={
                                    "nom":"Objet","quantite":"Qté","poids_kg":"Poids unit.","poids_total":"Poids total"
                                }), use_container_width=True, hide_index=True)

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
                    loc_opts   = ["soi"] + (["monture"] if monture_cur != "Aucune" else [])
                    loc_lbls   = ["🧍 Sur soi"] + ([f"🐴 Sur la {monture_cur}"] if monture_cur != "Aucune" else [])
                    loc_ch     = st.selectbox("Ranger où ?", loc_lbls, key="admin_add_loc")
                    loc_v      = loc_opts[loc_lbls.index(loc_ch)]

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
        # ── Infos joueur (monture + poids max) ──
        pinfo = load_player_info(user["id"])
        monture_actuelle = pinfo.get("monture") or "Aucune"
        poids_max = float(pinfo.get("poids_max_joueur") or 0)

        with st.expander("⚙️ Paramètres du personnage", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                monture_idx = MONTURES.index(monture_actuelle) if monture_actuelle in MONTURES else 0
                new_monture = st.selectbox("Type de monture", MONTURES, index=monture_idx, key="j_monture")
            with c2:
                new_poids_max = st.number_input("Poids max sur soi (kg)", min_value=0.0, value=poids_max, step=0.5, format="%.1f", key="j_poids_max")
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
            df_inv["poids_total"] = df_inv["poids_kg"] * df_inv["quantite"]
            df_soi      = df_inv[df_inv["localisation"] == "soi"]
            df_monture  = df_inv[df_inv["localisation"] == "monture"]
            poids_soi      = df_soi["poids_total"].sum()
            poids_monture  = df_monture["poids_total"].sum()
            poids_total    = df_inv["poids_total"].sum()

            # ── Métriques ──
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

            # ── Affichage Sur soi ──
            st.markdown("### 🧍 Sur soi")
            if df_soi.empty:
                st.caption("Aucun objet porté sur soi.")
            else:
                categories_soi = sorted(df_soi["categorie"].dropna().unique().tolist())
                for cat in categories_soi:
                    df_cat = df_soi[df_soi["categorie"] == cat].copy()
                    poids_cat = df_cat["poids_total"].sum()
                    nb_cat = df_cat["quantite"].sum()
                    with st.expander(f"⚔️ {cat}  —  {int(nb_cat)} objet(s)  •  {poids_cat:.2f} kg", expanded=True):
                        st.dataframe(
                            df_cat[["nom","quantite","poids_kg","poids_total","sous_categorie","notes"]].rename(columns={
                                "nom":"Objet","quantite":"Quantité","poids_kg":"Poids unit. (kg)",
                                "poids_total":"Poids total (kg)","sous_categorie":"Sous-catégorie","notes":"Notes"
                            }),
                            use_container_width=True, hide_index=True
                        )

            # ── Affichage Sur la monture ──
            if monture_actuelle != "Aucune":
                st.markdown(f"### 🐴 Sur la {monture_actuelle}")
                if df_monture.empty:
                    st.caption(f"Aucun objet sur la {monture_actuelle}.")
                else:
                    categories_mont = sorted(df_monture["categorie"].dropna().unique().tolist())
                    for cat in categories_mont:
                        df_cat = df_monture[df_monture["categorie"] == cat].copy()
                        poids_cat = df_cat["poids_total"].sum()
                        nb_cat = df_cat["quantite"].sum()
                        with st.expander(f"⚔️ {cat}  —  {int(nb_cat)} objet(s)  •  {poids_cat:.2f} kg", expanded=True):
                            st.dataframe(
                                df_cat[["nom","quantite","poids_kg","poids_total","sous_categorie","notes"]].rename(columns={
                                    "nom":"Objet","quantite":"Quantité","poids_kg":"Poids unit. (kg)",
                                    "poids_total":"Poids total (kg)","sous_categorie":"Sous-catégorie","notes":"Notes"
                                }),
                                use_container_width=True, hide_index=True
                            )

            # ── Déplacer / retirer un objet ──
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
        if df.empty:
            st.info("Le catalogue est vide.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                cats = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
                cat_filter = st.selectbox("Catégorie", cats, key="jcat")
            with c2:
                sub_df = df[df["categorie"] == cat_filter] if cat_filter != "Toutes" else df
                sous = ["Toutes"] + sorted(sub_df["sous_categorie"].dropna().unique().tolist())
                sous_filter = st.selectbox("Sous-catégorie", sous, key="jsous")
            with c3:
                search = st.text_input("🔍 Rechercher", placeholder="Nom...", key="jsearch")

            filtered = df.copy()
            if cat_filter  != "Toutes": filtered = filtered[filtered["categorie"]      == cat_filter]
            if sous_filter != "Toutes": filtered = filtered[filtered["sous_categorie"] == sous_filter]
            if search:                  filtered = filtered[filtered["nom"].str.contains(search, case=False, na=False)]

            st.markdown(f"**{len(filtered)}** objets")
            disp = ["categorie","sous_categorie","nom","poids_kg","prix_deniers","notes"]
            disp = [c for c in disp if c in filtered.columns]
            st.dataframe(
                filtered[disp].rename(columns={
                    "categorie":"Catégorie","sous_categorie":"Sous-catégorie",
                    "nom":"Nom","poids_kg":"Poids (kg)","prix_deniers":"Prix (deniers)","notes":"Notes"
                }),
                use_container_width=True, hide_index=True
            )

            st.markdown("---")
            st.markdown("##### Ajouter un objet à mon inventaire")
            c1, c2, c3 = st.columns(3)
            with c1:
                eq_list = sorted(filtered["nom"].tolist()) if not filtered.empty else sorted(df["nom"].tolist())
                chosen_eq = st.selectbox("Choisir l'objet", eq_list, key="jadd_eq")
            with c2:
                qty = st.number_input("Quantité", min_value=1, max_value=99, value=1, key="jadd_qty")
            with c3:
                pinfo2 = load_player_info(user["id"])
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
