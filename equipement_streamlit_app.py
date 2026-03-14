import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
import os
from datetime import datetime

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
.banner h1 {
    font-size: 2.8rem !important;
    text-shadow: 0 0 20px rgba(184,134,11,0.4);
}
.banner p {
    color: rgba(245,234,208,0.5);
    font-style: italic;
    font-size: 1.1rem;
}

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
#  SUPABASE
# ─────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url  = st.secrets["SUPABASE_URL"]
    key  = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ─────────────────────────────────────────────
#  AUTH HELPERS
# ─────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def login(username: str, password: str):
    result = supabase.table("users") \
        .select("*") \
        .eq("username", username) \
        .eq("password_hash", hash_password(password)) \
        .execute()
    if result.data:
        return result.data[0]
    return None

# ─────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_equipements():
    r = supabase.table("equipements").select("*").order("categorie").order("sous_categorie").order("nom").execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()

@st.cache_data(ttl=30)
def load_inventory(player_id: int):
    r = supabase.table("inventaire") \
        .select("*, equipements(*)") \
        .eq("player_id", player_id) \
        .execute()
    return r.data or []

@st.cache_data(ttl=30)
def load_players():
    r = supabase.table("users").select("id, username, role").eq("role", "joueur").execute()
    return r.data or []

def invalidate_cache():
    load_equipements.clear()
    load_inventory.clear()
    load_players.clear()

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
                if cat_filter != "Toutes":
                    sous = ["Toutes"] + sorted(df[df["categorie"] == cat_filter]["sous_categorie"].dropna().unique().tolist())
                else:
                    sous = ["Toutes"] + sorted(df["sous_categorie"].dropna().unique().tolist())
                sous_filter = st.selectbox("Sous-catégorie", sous)
            with c3:
                search = st.text_input("🔍 Rechercher", placeholder="Nom de l'objet...")

            filtered = df.copy()
            if cat_filter != "Toutes":
                filtered = filtered[filtered["categorie"] == cat_filter]
            if sous_filter != "Toutes":
                filtered = filtered[filtered["sous_categorie"] == sous_filter]
            if search:
                filtered = filtered[filtered["nom"].str.contains(search, case=False, na=False)]

            st.markdown(f"**{len(filtered)}** objets trouvés")
            display_cols = ["categorie", "sous_categorie", "nom", "poids_kg", "prix_deniers", "notes"]
            display_cols = [c for c in display_cols if c in filtered.columns]
            st.dataframe(
                filtered[display_cols].rename(columns={
                    "categorie": "Catégorie",
                    "sous_categorie": "Sous-catégorie",
                    "nom": "Nom",
                    "poids_kg": "Poids (kg)",
                    "prix_deniers": "Prix (deniers)",
                    "notes": "Notes"
                }),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.markdown("##### 🗑️ Supprimer un équipement")
            noms = sorted(df["nom"].tolist())
            to_delete = st.selectbox("Sélectionner l'objet à supprimer", noms)
            if st.button("Supprimer cet objet", type="primary"):
                obj_id = df[df["nom"] == to_delete]["id"].values[0]
                supabase.table("equipements").delete().eq("id", obj_id).execute()
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
                supabase.table("equipements").insert({
                    "categorie": new_cat.strip(),
                    "sous_categorie": new_sous.strip(),
                    "nom": new_nom.strip(),
                    "poids_kg": new_poids,
                    "prix_deniers": new_prix,
                    "notes": new_notes.strip(),
                }).execute()
                invalidate_cache()
                st.success(f"« {new_nom} » ajouté au catalogue !")
                st.rerun()
            else:
                st.warning("Le nom de l'objet est obligatoire.")

        st.markdown("---")
        st.markdown("#### Importer un fichier CSV")
        st.caption("Format attendu : Catégorie;Sous-catégorie;Nom;Poids (Kg);Prix (Deniers);Notes")
        uploaded = st.file_uploader("Choisir un fichier CSV", type=["csv"])
        if uploaded:
            try:
                df_import = pd.read_csv(uploaded, sep=";", encoding="latin-1")
                col_map = {
                    "Catégorie": "categorie",
                    "Sous-catégorie": "sous_categorie",
                    "Nom": "nom",
                    "Poids (Kg)": "poids_kg",
                    "Prix (Deniers)": "prix_deniers",
                    "Notes": "notes",
                }
                df_import = df_import.rename(columns=col_map)
                # Nettoyer les colonnes numériques
                if "poids_kg" in df_import.columns:
                    df_import["poids_kg"] = df_import["poids_kg"].astype(str).str.replace(",", ".").astype(float)
                if "prix_deniers" in df_import.columns:
                    df_import["prix_deniers"] = pd.to_numeric(df_import["prix_deniers"], errors="coerce").fillna(0).astype(int)
                if "notes" in df_import.columns:
                    df_import["notes"] = df_import["notes"].fillna("").astype(str)

                keep = [c for c in ["categorie", "sous_categorie", "nom", "poids_kg", "prix_deniers", "notes"] if c in df_import.columns]
                df_import = df_import[keep]

                st.dataframe(df_import.head(10), use_container_width=True)
                st.caption(f"{len(df_import)} objets détectés")

                if st.button("📥 Importer dans la base"):
                    records = df_import.to_dict(orient="records")
                    supabase.table("equipements").insert(records).execute()
                    invalidate_cache()
                    st.success(f"{len(records)} objets importés avec succès !")
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la lecture du CSV : {e}")

    # ── TAB 3 : Inventaires joueurs ──
    with tab3:
        players = load_players()
        if not players:
            st.info("Aucun joueur enregistré.")
        else:
            player_names = {p["username"]: p["id"] for p in players}
            selected_player = st.selectbox("Choisir un joueur", list(player_names.keys()))
            player_id = player_names[selected_player]

            inv = load_inventory(player_id)
            if not inv:
                st.info(f"{selected_player} ne possède aucun objet.")
            else:
                rows = []
                for item in inv:
                    eq = item.get("equipements", {}) or {}
                    rows.append({
                        "inv_id": item["id"],
                        "Objet": eq.get("nom", "?"),
                        "Quantité": item.get("quantite", 1),
                        "Poids unitaire (kg)": eq.get("poids_kg", 0),
                        "Poids total (kg)": round(eq.get("poids_kg", 0) * item.get("quantite", 1), 3),
                        "Catégorie": eq.get("categorie", ""),
                    })
                df_inv = pd.DataFrame(rows)
                poids_total = df_inv["Poids total (kg)"].sum()

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""<div class="metric-card">
                        <div class="metric-value">{len(df_inv)}</div>
                        <div class="metric-label">Objets différents</div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="metric-card">
                        <div class="metric-value">{poids_total:.2f} kg</div>
                        <div class="metric-label">Poids total porté</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")
                st.dataframe(df_inv.drop(columns=["inv_id"]), use_container_width=True, hide_index=True)

                # Retirer un objet de l'inventaire joueur
                st.markdown("---")
                st.markdown("##### Retirer un objet de l'inventaire")
                obj_names = df_inv["Objet"].tolist()
                to_remove = st.selectbox("Objet à retirer", obj_names, key="admin_remove")
                if st.button("🗑️ Retirer", key="admin_remove_btn"):
                    inv_id = df_inv[df_inv["Objet"] == to_remove]["inv_id"].values[0]
                    supabase.table("inventaire").delete().eq("id", inv_id).execute()
                    invalidate_cache()
                    st.success(f"« {to_remove} » retiré de l'inventaire de {selected_player}.")
                    st.rerun()

            # Ajouter un objet à l'inventaire d'un joueur
            st.markdown("---")
            st.markdown("##### Ajouter un objet à l'inventaire")
            df_eq = load_equipements()
            if not df_eq.empty:
                eq_names = sorted(df_eq["nom"].tolist())
                chosen_eq = st.selectbox("Choisir l'objet", eq_names, key="admin_add_eq")
                qty = st.number_input("Quantité", min_value=1, max_value=99, value=1, key="admin_add_qty")
                if st.button("➕ Ajouter à l'inventaire"):
                    eq_id = df_eq[df_eq["nom"] == chosen_eq]["id"].values[0]
                    supabase.table("inventaire").insert({
                        "player_id": player_id,
                        "equipement_id": int(eq_id),
                        "quantite": qty,
                    }).execute()
                    invalidate_cache()
                    st.success(f"« {chosen_eq} » (x{qty}) ajouté à l'inventaire de {selected_player}.")
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
                    supabase.table("users").insert({
                        "username": new_username.strip(),
                        "password_hash": hash_password(new_password),
                        "role": "joueur",
                    }).execute()
                    invalidate_cache()
                    st.success(f"Compte joueur « {new_username} » créé.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Nom d'utilisateur et mot de passe requis.")

        st.markdown("---")
        st.markdown("#### Joueurs enregistrés")
        players = load_players()
        if players:
            for p in players:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"🧙 **{p['username']}**")
                with col2:
                    if st.button("Supprimer", key=f"del_{p['id']}"):
                        supabase.table("users").delete().eq("id", p["id"]).execute()
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

    # ── TAB 1 : Inventaire ──
    with tab1:
        inv = load_inventory(user["id"])

        if not inv:
            st.info("Votre besace est vide. Consultez le catalogue pour vous équiper.")
        else:
            rows = []
            for item in inv:
                eq = item.get("equipements", {}) or {}
                rows.append({
                    "inv_id": item["id"],
                    "Objet": eq.get("nom", "?"),
                    "Quantité": item.get("quantite", 1),
                    "Poids unitaire (kg)": eq.get("poids_kg", 0),
                    "Poids total (kg)": round(eq.get("poids_kg", 0) * item.get("quantite", 1), 3),
                    "Catégorie": eq.get("categorie", ""),
                    "Notes": eq.get("notes", ""),
                })
            df_inv = pd.DataFrame(rows)
            poids_total = df_inv["Poids total (kg)"].sum()
            nb_objets   = df_inv["Quantité"].sum()

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{len(df_inv)}</div>
                    <div class="metric-label">Types d'objets</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{int(nb_objets)}</div>
                    <div class="metric-label">Objets au total</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value">{poids_total:.2f} kg</div>
                    <div class="metric-label">Poids porté</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")
            st.dataframe(
                df_inv.drop(columns=["inv_id"]),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.markdown("##### Retirer un objet")
            to_remove = st.selectbox("Objet à retirer", df_inv["Objet"].tolist())
            if st.button("🗑️ Retirer de mon inventaire"):
                inv_id = df_inv[df_inv["Objet"] == to_remove]["inv_id"].values[0]
                supabase.table("inventaire").delete().eq("id", inv_id).execute()
                invalidate_cache()
                st.success(f"« {to_remove} » retiré de votre inventaire.")
                st.rerun()

    # ── TAB 2 : Catalogue ──
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
                if cat_filter != "Toutes":
                    sous = ["Toutes"] + sorted(df[df["categorie"] == cat_filter]["sous_categorie"].dropna().unique().tolist())
                else:
                    sous = ["Toutes"] + sorted(df["sous_categorie"].dropna().unique().tolist())
                sous_filter = st.selectbox("Sous-catégorie", sous, key="jsous")
            with c3:
                search = st.text_input("🔍 Rechercher", placeholder="Nom...", key="jsearch")

            filtered = df.copy()
            if cat_filter != "Toutes":
                filtered = filtered[filtered["categorie"] == cat_filter]
            if sous_filter != "Toutes":
                filtered = filtered[filtered["sous_categorie"] == sous_filter]
            if search:
                filtered = filtered[filtered["nom"].str.contains(search, case=False, na=False)]

            st.markdown(f"**{len(filtered)}** objets")
            display_cols = ["categorie", "sous_categorie", "nom", "poids_kg", "prix_deniers", "notes"]
            display_cols = [c for c in display_cols if c in filtered.columns]
            st.dataframe(
                filtered[display_cols].rename(columns={
                    "categorie": "Catégorie",
                    "sous_categorie": "Sous-catégorie",
                    "nom": "Nom",
                    "poids_kg": "Poids (kg)",
                    "prix_deniers": "Prix (deniers)",
                    "notes": "Notes"
                }),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.markdown("##### Ajouter un objet à mon inventaire")
            eq_names = sorted(filtered["nom"].tolist()) if not filtered.empty else sorted(df["nom"].tolist())
            chosen_eq = st.selectbox("Choisir l'objet", eq_names, key="jadd_eq")
            qty = st.number_input("Quantité", min_value=1, max_value=99, value=1, key="jadd_qty")
            if st.button("➕ Ajouter à mon inventaire"):
                eq_id = df[df["nom"] == chosen_eq]["id"].values[0]
                supabase.table("inventaire").insert({
                    "player_id": user["id"],
                    "equipement_id": int(eq_id),
                    "quantite": qty,
                }).execute()
                invalidate_cache()
                st.success(f"« {chosen_eq} » (x{qty}) ajouté à votre inventaire !")
                st.rerun()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
def sidebar():
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
sidebar()

if st.session_state.user is None:
    page_login()
elif st.session_state.user["role"] == "admin":
    page_admin()
else:
    page_joueur()
