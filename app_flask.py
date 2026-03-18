# app_flask.py
"""
Assistance IA Télécom — Interface Flask
Utilise le backend chatbot/ existant avec une interface HTML/CSS/JS pure.
Usage: python app_flask.py
"""

import os, json, tempfile, base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from gtts import gTTS
from chatbot.config import APP_TITLE, FAISS_INDEX_PATH
from chatbot.database import (
    init_database, register_user, login_user,
    create_conversation, get_user_conversations,
    add_message, get_conversation_messages,
    update_conversation_title, delete_conversation
)
from chatbot.rag_pipeline import get_answer, search_faiss

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)

import re

@app.template_filter('md')
def markdown_filter(text):
    """Convertit le markdown basique en HTML."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = text.replace('\n', '<br>')
    return text

# Dossier audio temporaire
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

init_database()


# ── Helpers ──

def logged_in():
    return "user" in session


def get_user():
    return session.get("user")


def make_audio(text, msg_id):
    """Génère un fichier audio et retourne le chemin relatif."""
    path = os.path.join(AUDIO_DIR, f"{msg_id}.mp3")
    if not os.path.exists(path):
        try:
            tts = gTTS(text=text, lang='fr')
            tts.save(path)
        except:
            return None
    return f"/static/audio/{msg_id}.mp3"


# ── Routes Auth ──

@app.route("/")
def index():
    if logged_in():
        return redirect(url_for("chat"))
    return render_template("login.html", title=APP_TITLE, mode="login")


@app.route("/login", methods=["POST"])
def do_login():
    data = request.json
    result = login_user(data["email"], data["password"])
    if result["success"]:
        session["user"] = result["user"]
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": result["error"]})


@app.route("/register", methods=["POST"])
def do_register():
    data = request.json
    result = register_user(data["nom"], data["prenom"], data["email"], data["password"])
    if result["success"]:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": result["error"]})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ── Routes Chat ──

@app.route("/chat")
def chat():
    if not logged_in():
        return redirect(url_for("index"))
    user = get_user()
    convs = get_user_conversations(user["id"])
    conv_id = request.args.get("conv_id", type=int)

    messages = []
    if conv_id:
        messages = get_conversation_messages(conv_id)
        # Générer audio pour chaque réponse bot
        for i, msg in enumerate(messages):
            if msg["role"] == "assistant":
                audio_id = f"{conv_id}_{i}"
                msg["audio"] = make_audio(msg["content"], audio_id)

    return render_template("chat.html",
        title=APP_TITLE, user=user, convs=convs,
        conv_id=conv_id, messages=messages, page="chat")


@app.route("/ask", methods=["POST"])
def do_ask():
    if not logged_in():
        return jsonify({"ok": False, "error": "Non connecté"})

    try:
        data = request.json
        query = data.get("query", "").strip()
        conv_id = data.get("conv_id")
        user = get_user()

        if len(query.split()) < 2:
            return jsonify({"ok": False, "error": "Question trop courte (min. 2 mots)"})

        # Créer conversation si nécessaire
        if not conv_id:
            conv_id = create_conversation(user["id"])
            update_conversation_title(conv_id, query[:50] + ("..." if len(query) > 50 else ""))

        # RAG pipeline
        results = search_faiss(query, top_n=5)
        context = "\n\n".join([doc for doc, _ in results])

        # Historique récent
        history = get_conversation_messages(conv_id)[-6:]
        response = get_answer(query, context, history if history else None)

        # Sauvegarder
        add_message(conv_id, "user", query)
        add_message(conv_id, "assistant", response)

        # Audio
        msg_count = len(get_conversation_messages(conv_id))
        audio_url = make_audio(response, f"{conv_id}_{msg_count}")

        return jsonify({
            "ok": True,
            "response": response,
            "conv_id": conv_id,
            "audio": audio_url
        })
    except Exception as e:
        print(f"ERREUR /ask: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


@app.route("/new_conv", methods=["POST"])
def new_conv():
    if not logged_in():
        return jsonify({"ok": False})
    conv_id = create_conversation(get_user()["id"])
    return jsonify({"ok": True, "conv_id": conv_id})


@app.route("/delete_conv/<int:conv_id>", methods=["POST"])
def del_conv(conv_id):
    delete_conversation(conv_id)
    return jsonify({"ok": True})


# ── Routes Pages ──

@app.route("/history")
def history():
    if not logged_in():
        return redirect(url_for("index"))
    user = get_user()
    convs = get_user_conversations(user["id"])
    return render_template("page.html", title=APP_TITLE, user=user, convs=convs, page="history")


@app.route("/settings")
def settings():
    if not logged_in():
        return redirect(url_for("index"))
    return render_template("page.html", title=APP_TITLE, user=get_user(), convs=get_user_conversations(get_user()["id"]), page="settings")


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if not logged_in():
        return redirect(url_for("index"))
    if request.method == "POST":
        import pandas as pd, time
        data = request.json
        user = get_user()
        df = pd.DataFrame({
            "user": [user["email"]], "nom": [f"{user['prenom']} {user['nom']}"],
            "satisfaction": [data["satisfaction"]], "feedback": [data["feedback"]],
            "date": [time.strftime("%Y-%m-%d %H:%M")]
        })
        fp = os.path.join(os.path.dirname(__file__), "feedback.csv")
        df.to_csv(fp, mode='a', header=not os.path.exists(fp), index=False)
        return jsonify({"ok": True})
    return render_template("page.html", title=APP_TITLE, user=get_user(), convs=get_user_conversations(get_user()["id"]), page="feedback")


@app.route("/about")
def about():
    if not logged_in():
        return redirect(url_for("index"))
    return render_template("page.html", title=APP_TITLE, user=get_user(), convs=get_user_conversations(get_user()["id"]), page="about")


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    pdf_dir = os.path.join(os.path.dirname(__file__), "pdf_files")
    os.makedirs(pdf_dir, exist_ok=True)
    files = request.files.getlist("pdfs")
    count = 0
    for f in files:
        if f.filename and f.filename.endswith(".pdf"):
            dest = os.path.join(pdf_dir, f.filename)
            if not os.path.exists(dest):
                f.save(dest)
                count += 1
    return jsonify({"ok": True, "count": count})


@app.route("/widget-demo")
def widget_demo():
    return render_template("widget_demo.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
