# app.py
"""
Assistance IA Télécom — Version Finale
- Sidebar = menu (glisser sur mobile, ☰ indiqué en haut)
- Micro via audio_recorder_streamlit
- Pages : Chat, Historique, Paramètres, Feedback, À propos
"""

import streamlit as st
import os, time, base64, tempfile, urllib.parse
import pandas as pd
from gtts import gTTS

from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.memory import ChatMemory
from chatbot.config import APP_TITLE, APP_ICON
from chatbot.database import (
    register_user, login_user,
    create_conversation, get_user_conversations,
    add_message, get_conversation_messages,
    update_conversation_title, delete_conversation
)

_favicon = os.path.join(os.path.dirname(__file__), "assets", "favicon.png")
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=_favicon if os.path.exists(_favicon) else APP_ICON,
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ── Utils ──

def load_css():
    st.markdown('<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">', unsafe_allow_html=True)
    p = os.path.join(os.path.dirname(__file__), "css", "styles.css")
    if os.path.exists(p):
        with open(p) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def apply_theme(t):
    if t == "dark":
        st.markdown("""<style>
        :root{--bg:#0e0b1e;--bg2:#1a1535;--txt:#e8e5f5;--txt2:#9490ad;--acc:#8b7ff5;--acc-g:rgba(139,127,245,.3);--acc-s:#1e1845;--ubub:linear-gradient(135deg,#6c5ce7,#a29bfe);--bbub:#1a1535;--btxt:#e8e5f5;--brd:#2a2550;--inp:#1a1535}
        .stApp{background:#0e0b1e!important}
        section[data-testid="stSidebar"]{background:#1a1535!important}
        p,span,label,.stMarkdown{color:#e8e5f5!important}
        h1,h2,h3,h4,h5{color:#8b7ff5!important}
        .stTextInput input,.stTextArea textarea{background:#1a1535!important;color:#e8e5f5!important;border-color:#2a2550!important}
        </style>""", unsafe_allow_html=True)


def img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def make_audio(text):
    try:
        tts = gTTS(text=text, lang='fr')
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(t.name)
        return t.name
    except:
        return None


def mini_audio_player(filepath):
    """Mini player HTML compact comme dans le mockup."""
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <div style="padding-left:30px;margin:4px 0 10px;">
        <audio controls style="height:28px;width:180px;border-radius:8px;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    </div>
    """, unsafe_allow_html=True)


def init():
    for k, v in {"user": None, "conv_id": None, "mem": ChatMemory(), "theme": "light",
                  "show_reg": False, "audio": {}, "page": "chat", "pq": None}.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Process Query ──

def ask(query):
    if len(query.split()) < 2:
        st.toast("⚠️ Question trop courte")
        return
    u = st.session_state.user
    if not st.session_state.conv_id:
        cid = create_conversation(u["id"])
        st.session_state.conv_id = cid
        update_conversation_title(cid, query[:50] + ("..." if len(query) > 50 else ""))
    with st.spinner("💡 Analyse en cours..."):
        res = search_faiss(query, top_n=5)
        ctx = "\n\n".join([d for d, _ in res])
        mem = st.session_state.mem.get_context()
        ans = get_answer(query, ctx, mem)
    st.session_state.mem.add_message("user", query)
    st.session_state.mem.add_message("assistant", ans)
    add_message(st.session_state.conv_id, "user", query)
    add_message(st.session_state.conv_id, "assistant", ans)
    st.rerun()


# ── Top Bar avec menu fonctionnel ──

def topbar():
    c1, c2 = st.columns([7, 1])
    with c1:
        st.markdown(f"<span style='font-size:13px;font-weight:600;color:#1b1340;font-family:Outfit,sans-serif;letter-spacing:-0.02em'>📡 {APP_TITLE}</span>", unsafe_allow_html=True)
    with c2:
        u = st.session_state.user
        with st.popover("☰"):
            st.caption(f"{u['prenom']} {u['nom']} — {u['email']}")
            for icon, label, pg in [("➕","Nouvelle conv.","__new"),("💬","Chat","chat"),("📚","Historique","history"),
                                    ("⚙️","Paramètres","settings"),("📝","Feedback","feedback"),("ℹ️","À propos","about")]:
                if st.button(f"{icon} {label}", key=f"m_{pg}", use_container_width=True):
                    if pg == "__new":
                        cid = create_conversation(u["id"]); st.session_state.conv_id = cid
                        st.session_state.mem = ChatMemory(); st.session_state.page = "chat"
                    else:
                        st.session_state.page = pg
                    st.rerun()
            st.divider()
            ti = "🌙" if st.session_state.theme == "light" else "☀️"
            if st.button(f"{ti} Thème", key="m_th", use_container_width=True):
                st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"; st.rerun()
            if st.button("🚪 Quitter", key="m_out", use_container_width=True):
                for k in list(st.session_state.keys()): del st.session_state[k]
                st.rerun()
    st.markdown("<hr style='margin:2px 0 8px;border-color:#e4e2ec;opacity:0.4'>", unsafe_allow_html=True)


# ── Sidebar Menu ──

def sidebar_menu():
    u = st.session_state.user
    with st.sidebar:
        st.markdown(f"""
        <div class='sidebar-profile'>
            <div class='profile-avatar'>👤</div>
            <div class='profile-info'>
                <strong>{u['prenom']} {u['nom']}</strong><br>
                <span class='profile-email'>{u['email']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        for icon, label, pg in [("💬","Chat","chat"),("📚","Historique","history"),
                                ("⚙️","Paramètres","settings"),("📝","Feedback","feedback"),
                                ("ℹ️","À propos","about")]:
            active = st.session_state.page == pg
            if st.button(f"{icon} {label}", key=f"nav_{pg}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.page = pg
                st.rerun()

        st.markdown("---")
        if st.button("➕ Nouvelle conversation", key="nav_new", use_container_width=True):
            cid = create_conversation(u["id"])
            st.session_state.conv_id = cid
            st.session_state.mem = ChatMemory()
            st.session_state.page = "chat"
            st.rerun()

        ti = "🌙" if st.session_state.theme == "light" else "☀️"
        tl = "Mode sombre" if st.session_state.theme == "light" else "Mode clair"
        if st.button(f"{ti} {tl}", key="nav_theme", use_container_width=True):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Déconnexion", key="nav_out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── Login (style Claude — centré, card, minimaliste) ──

def login_page():
    # Spacer haut
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)

    # Logo centré
    logo = img_b64(os.path.join(os.path.dirname(__file__), "assets", "ia_telecom.png"))
    if logo:
        st.markdown(f"<div style='text-align:center;margin-bottom:1.2rem'><img src='data:image/png;base64,{logo}' style='width:64px;height:64px;border-radius:16px;box-shadow:0 6px 20px rgba(91,76,219,0.25)'/></div>", unsafe_allow_html=True)

    # Titre + sous-titre
    st.markdown("""
    <div style='text-align:center;margin-bottom:2rem'>
        <h1 style='font-family:Outfit,sans-serif;font-size:1.6rem;font-weight:700;color:#1b1340;margin:0 0 4px;letter-spacing:-0.03em'>Assistance IA Télécom</h1>
        <p style='color:#6e6b7b;font-size:0.9rem;margin:0'>Votre assistant réglementaire intelligent</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.show_reg:
        st.markdown("<p style='text-align:center;font-weight:600;font-size:0.95rem;color:#1b1340;margin-bottom:0.5rem'>Créer un compte</p>", unsafe_allow_html=True)
        with st.form("reg"):
            nom = st.text_input("a", placeholder="Nom", label_visibility="collapsed")
            pre = st.text_input("b", placeholder="Prénom", label_visibility="collapsed")
            em = st.text_input("c", placeholder="Email", label_visibility="collapsed")
            pw = st.text_input("d", type="password", placeholder="Mot de passe (min. 4 caractères)", label_visibility="collapsed")
            pw2 = st.text_input("e", type="password", placeholder="Confirmer le mot de passe", label_visibility="collapsed")
            if st.form_submit_button("S'inscrire", use_container_width=True):
                if all([nom, pre, em, pw, pw2]) and len(pw) >= 4 and pw == pw2:
                    r = register_user(nom, pre, em, pw)
                    if r["success"]:
                        st.success("✅ Compte créé avec succès !")
                        st.session_state.show_reg = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(r["error"])
                else:
                    st.warning("Vérifiez les champs.")
        if st.button("← Déjà un compte ? Se connecter", use_container_width=True, type="secondary"):
            st.session_state.show_reg = False
            st.rerun()
    else:
        st.markdown("<p style='text-align:center;font-weight:600;font-size:0.95rem;color:#1b1340;margin-bottom:0.5rem'>Se connecter</p>", unsafe_allow_html=True)
        with st.form("log"):
            em = st.text_input("x", placeholder="Email", label_visibility="collapsed")
            pw = st.text_input("y", type="password", placeholder="Mot de passe", label_visibility="collapsed")
            if st.form_submit_button("Continuer", use_container_width=True):
                if em and pw:
                    r = login_user(em, pw)
                    if r["success"]:
                        st.session_state.user = r["user"]
                        st.session_state.mem = ChatMemory()
                        st.rerun()
                    else:
                        st.error(r["error"])
                else:
                    st.warning("Remplissez tous les champs.")
        if st.button("Pas encore de compte ? S'inscrire", use_container_width=True, type="secondary"):
            st.session_state.show_reg = True
            st.rerun()

    # Footer
    st.markdown("<p style='text-align:center;color:#9490ad;font-size:0.7rem;margin-top:2rem'>Projet de mémoire — 2024/2025</p>", unsafe_allow_html=True)


# ── Page Chat ──

def page_chat():
    if st.session_state.pq:
        q = st.session_state.pq
        st.session_state.pq = None
        ask(q)
        return

    hist = st.session_state.mem.get_formatted_history()

    if not hist:
        logo = img_b64(os.path.join(os.path.dirname(__file__), "assets", "ia_telecom.png"))
        st.markdown("<div class='welcome-spacer'></div>", unsafe_allow_html=True)
        if logo:
            st.markdown(f"<div class='welcome-logo'><img src='data:image/png;base64,{logo}'/></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center;font-size:3rem'>📡</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class='welcome-text'>
            <h2>Comment puis-je vous aider ?</h2>
            <p>Posez vos questions sur la réglementation des<br>télécommunications au Burkina Faso</p>
        </div>
        """, unsafe_allow_html=True)

        for icon, txt in [("📋", "Conditions d'une licence télécom au Burkina Faso"),
                          ("📡", "Quelles sont les obligations des opérateurs télécom"),
                          ("⚖️", "Quelles sanctions sont prévues par la loi")]:
            if st.button(f"{icon} {txt}", key=f"s_{icon}", use_container_width=True, type="secondary"):
                st.session_state.pq = txt
                st.rerun()
    else:
        for idx, ex in enumerate(hist):
            st.markdown(f"<div class='msg-row user-row'><div class='msg-bubble user-bubble'>{ex['user']}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg-row bot-row'><div class='msg-avatar'>📡</div><div class='msg-bubble bot-bubble'>{ex['bot']}</div></div>", unsafe_allow_html=True)
            ak = f"a_{idx}"
            if ak not in st.session_state.audio:
                p = make_audio(ex["bot"])
                if p:
                    st.session_state.audio[ak] = p
            if ak in st.session_state.audio:
                st.audio(st.session_state.audio[ak], format="audio/mp3")

    # Input natif Streamlit
    q = st.chat_input("Posez votre question ici...")
    if q:
        ask(q)


# ── Page Historique ──

def page_history():
    u = st.session_state.user
    st.markdown("<div class='page-header'><h2>📚 Historique</h2><p>Vos conversations passées</p></div>", unsafe_allow_html=True)
    if st.button("➕ Nouvelle conversation", use_container_width=True, type="primary"):
        cid = create_conversation(u["id"])
        st.session_state.conv_id = cid
        st.session_state.mem = ChatMemory()
        st.session_state.page = "chat"
        st.rerun()
    st.markdown("---")
    convs = get_user_conversations(u["id"])
    if not convs:
        st.info("Aucune conversation pour le moment.")
        return
    for c in convs:
        active = st.session_state.conv_id == c["id"]
        dt = c.get("updated_at", "")[:16] if c.get("updated_at") else ""
        st.markdown(f"<div class='conv-card {'conv-active' if active else ''}'><div class='conv-title'>{'▸ ' if active else ''}{c['title']}</div><div class='conv-date'>{dt}</div></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button("Ouvrir", key=f"o_{c['id']}", use_container_width=True):
                st.session_state.conv_id = c["id"]
                st.session_state.mem = ChatMemory()
                for m in get_conversation_messages(c["id"]):
                    st.session_state.mem.add_message(m["role"], m["content"])
                st.session_state.page = "chat"
                st.rerun()
        with c2:
            if st.button("🗑", key=f"d_{c['id']}"):
                delete_conversation(c["id"])
                if st.session_state.conv_id == c["id"]:
                    st.session_state.conv_id = None
                    st.session_state.mem = ChatMemory()
                st.rerun()


# ── Page Paramètres ──

def page_settings():
    u = st.session_state.user
    st.markdown("<div class='page-header'><h2>⚙️ Paramètres</h2></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='settings-card'><div class='settings-icon'>👤</div><div><strong>{u['prenom']} {u['nom']}</strong><br><span style='color:#6e6b7b;font-size:0.85rem'>{u['email']}</span></div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 🎨 Apparence")
    ti = "🌙" if st.session_state.theme == "light" else "☀️"
    tl = "Passer en mode sombre" if st.session_state.theme == "light" else "Passer en mode clair"
    if st.button(f"{ti} {tl}", use_container_width=True):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    st.markdown("---")
    st.markdown("##### 📂 Ajouter des documents PDF")
    files = st.file_uploader("PDF", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
    if files:
        d = os.path.join(os.path.dirname(__file__), "pdf_files")
        os.makedirs(d, exist_ok=True)
        n = 0
        for f in files:
            p = os.path.join(d, f.name)
            if not os.path.exists(p):
                with open(p, "wb") as o:
                    o.write(f.getbuffer())
                n += 1
        if n:
            st.success(f"✅ {n} fichier(s) ajouté(s). Relancez `python init_index.py`.")

    st.markdown("---")
    if st.button("🧹 Effacer la conversation actuelle", use_container_width=True, type="secondary"):
        if st.session_state.conv_id:
            delete_conversation(st.session_state.conv_id)
        st.session_state.conv_id = None
        st.session_state.mem = ChatMemory()
        st.session_state.page = "chat"
        st.rerun()


# ── Page Feedback ──

def page_feedback():
    st.markdown("<div class='page-header'><h2>📝 Feedback</h2></div>", unsafe_allow_html=True)
    u = st.session_state.user
    sat = st.slider("Satisfaction", 1, 5, 3, format="%d ⭐")
    fb = st.text_area("Commentaire", placeholder="Votre retour...", height=120)
    if st.button("📨 Envoyer", use_container_width=True, type="primary"):
        if fb:
            df = pd.DataFrame({"user": [u["email"]], "nom": [f"{u['prenom']} {u['nom']}"],
                                "satisfaction": [sat], "feedback": [fb], "date": [time.strftime("%Y-%m-%d %H:%M")]})
            fp = os.path.join(os.path.dirname(__file__), "feedback.csv")
            df.to_csv(fp, mode='a', header=not os.path.exists(fp), index=False)
            st.success("✅ Merci !")
            st.balloons()
    fp = os.path.join(os.path.dirname(__file__), "feedback.csv")
    if os.path.exists(fp):
        st.markdown("---")
        st.markdown("##### 📊 Avis reçus")
        try:
            df = pd.read_csv(fp)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Moyenne", f"{df['satisfaction'].mean():.1f} / 5 ⭐")
        except:
            pass


# ── Page À propos ──

def page_about():
    st.markdown("<div class='page-header'><h2>ℹ️ À propos</h2></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='about-card'>
        <div style='font-size:2.5rem;margin-bottom:.5rem'>📡</div>
        <h3>Assistance IA Télécom</h3>
        <span class='version-badge'>Version 2.0</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    for title, content in [
        ("🎯 Description", "Chatbot RAG utilisant <strong>FAISS</strong> + <strong>Gemini 2.5 Flash</strong> pour la réglementation télécom au Burkina Faso."),
        ("🔧 Technologies", "• Streamlit<br>• FAISS<br>• Sentence Transformers<br>• Gemini 2.5 Flash<br>• PyMuPDF<br>• SQLite<br>• gTTS + Web Speech API"),
        ("📊 Pipeline RAG", "1. Extraction PDF → 2. Chunking 500 mots → 3. Embeddings → 4. FAISS → 5. Top 5 chunks → 6. Gemini"),
        ("📱 Fonctionnalités", "• Authentification sécurisée<br>• Sauvegarde des conversations<br>• Thème sombre/clair<br>• Audio des réponses<br>• Entrée vocale (long-press)<br>• Upload de PDF<br>• Feedback utilisateur"),
        ("👨‍💻 Réalisation", "Projet de mémoire — 2024/2025"),
    ]:
        st.markdown(f"<div class='about-section'><h4>{title}</h4><p>{content}</p></div>", unsafe_allow_html=True)


# ── Main ──

def main():
    init()
    load_css()
    apply_theme(st.session_state.theme)

    # Récupérer la query depuis le composant custom (texte ou vocal)
    params = st.query_params
    q = params.get("q")
    if q and st.session_state.user:
        decoded = urllib.parse.unquote(str(q))
        st.query_params.clear()
        st.session_state.page = "chat"
        ask(decoded)
        return

    if not st.session_state.user:
        login_page()
        return

    topbar()
    sidebar_menu()
    {"chat": page_chat, "history": page_history, "settings": page_settings,
     "feedback": page_feedback, "about": page_about}[st.session_state.page]()


if __name__ == "__main__":
    main()
