import os
import base64
import sqlite3
import hashlib
import streamlit as st

from chunker import chunk_text
from rag_engine import ask_llm
from transcriber import download_audio, transcribe
from tts import speak
from vector_store import VectorStore


DEFAULT_LOGO_PATH = "/home/elkanavilvine/.cursor/projects/home-elkanavilvine-youtube-rag-ai/assets/Untitled-a30ffc03-90b7-48e5-ae0b-d468239c100e.png"
LOGO_PATH = os.getenv("WATCHWISE_LOGO_PATH", DEFAULT_LOGO_PATH)
DEFAULT_TAB_ICON_PATH = "/home/elkanavilvine/.cursor/projects/home-elkanavilvine-youtube-rag-ai/assets/image-dd6a4cd9-6832-4455-aa4e-c64688f0609a.png"
USERS_DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def image_to_data_uri(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_auth_db():
    with sqlite3.connect(USERS_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_user(username, email, password):
    if not username or not email or not password:
        return False, "All fields are required."

    with sqlite3.connect(USERS_DB_PATH) as conn:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing:
            return False, "Username already exists. Please login."

        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, _hash_password(password)),
        )
        conn.commit()
    return True, "Sign up successful. Please login."


def validate_login(username, password):
    with sqlite3.connect(USERS_DB_PATH) as conn:
        user_row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if not user_row:
        return False, "Account not found. Please sign up."
    if user_row[0] != _hash_password(password):
        return False, "Invalid username or password."
    return True, "Login successful."


def _format_srt_time(seconds):
    total_ms = int(seconds * 1000)
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    secs = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def build_srt(subtitle_segments):
    lines = []
    for idx, segment in enumerate(subtitle_segments, start=1):
        start = _format_srt_time(segment["start"])
        end = _format_srt_time(segment["end"])
        text = segment["text"].strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


st.set_page_config(
    page_title="Watch-Wise.ai",
    page_icon=DEFAULT_TAB_ICON_PATH if os.path.exists(DEFAULT_TAB_ICON_PATH) else "🤖",
    layout="wide",
)


st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

        :root {
            --bg: #eeefde;
            --panel: rgba(255, 255, 255, 0.62);
            --panel-strong: #f9f9ef;
            --ink: #121212;
            --ink-soft: #4d4d4d;
            --accent: #ddb8ff;
            --accent-dark: #6c2f90;
            --mint: #0d6456;
            --line: rgba(13, 100, 86, 0.18);
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: var(--ink);
        }

        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 10% 10%, #f3f4e8 0%, var(--bg) 36%, #e8e8d8 100%);
        }

        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            left: 50%;
            top: 52%;
            transform: translate(-50%, -50%);
            width: min(30vw, 360px);
            height: min(18vw, 210px);
            background-repeat: no-repeat;
            background-position: center top;
            background-size: 100% auto;
            opacity: 0.09;
            pointer-events: none;
            z-index: 0;
        }

        [data-testid="stAppViewContainer"] > .main {
            position: relative;
            z-index: 1;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: rgb(255 255 255 / 90%);

            border-right: 1px solid var(--line);
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.8rem;
            padding-bottom: 2rem;
        }

        .top-banner {
            background: linear-gradient(90deg, #7000b8, #8d00d4);
            color: #f7ecff;
            border-radius: 14px;
            padding: 0.6rem 1rem;
            margin-bottom: 0.65rem;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 10px 24px rgba(86, 14, 125, 0.22);
        }

        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            font-size: 0.88rem;
        }

        .top-nav-left {
            display: flex;
            align-items: center;
            gap: 1.1rem;
        }

        .top-nav-brand {
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 0.02em;
            color: #ffffff;
        }

        .top-nav-links {
            color: rgba(245, 236, 255, 0.92);
            font-size: 0.82rem;
            white-space: nowrap;
        }

        .auth-shell {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.7rem;
        }

        .hero-wrap {
            background: var(--panel);
            border: 1px solid rgba(18, 18, 18, 0.06);
            border-radius: 28px;
            backdrop-filter: blur(6px);
            padding: 2rem 2rem 1.8rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 16px 38px rgba(35, 35, 35, 0.09);
        }

        .hero-headline {
            text-align: center;
            line-height: 1.05;
            margin-bottom: 0.7rem;
        }

        .hero-headline .soft {
            font-family: 'Playfair Display', serif;
            font-size: clamp(2rem, 5vw, 3.35rem);
            color: #a8a895;
            font-weight: 600;
            margin-right: 0.35rem;
        }

        .hero-headline .strong {
            font-family: 'Playfair Display', serif;
            font-size: clamp(2rem, 5vw, 3.35rem);
            color: #171717;
            font-weight: 700;
        }

        .hero-sub {
            max-width: 700px;
            text-align: center;
            margin: 0 auto 1.4rem;
            color: var(--ink-soft);
            font-size: 1rem;
        }

        .workflow-note {
            text-align: center;
            color: #5c5c52;
            font-size: 0.86rem;
            margin-top: 0.4rem;
            margin-bottom: 0.2rem;
        }

        .card {
            background: var(--panel-strong);
            border: 1px solid rgba(18, 18, 18, 0.08);
            border-radius: 18px;
            padding: 1.15rem 1.1rem;
            box-shadow: 0 8px 24px rgba(40, 40, 40, 0.06);
            height: 100%;
        }

        .card h4 {
            margin: 0 0 0.6rem;
            font-size: 1rem;
        }

        .status-chip {
            background: #f3e7ff;
            color: var(--accent-dark);
            border: 1px solid rgba(108, 47, 144, 0.2);
            border-radius: 999px;
            padding: 0.26rem 0.65rem;
            font-size: 0.8rem;
            display: inline-block;
            margin-bottom: 0.7rem;
        }

        div[data-testid="stTextInput"] > div > div,
        div[data-testid="stTextArea"] > div > div {
            border-radius: 13px;
            border: 1px solid rgba(18, 18, 18, 0.15);
            background: rgba(255, 255, 255, 0.8);
        }

        .stButton > button {
            width: 100%;
            border-radius: 999px;
            border: 1px solid #161616;
            padding: 0.58rem 1rem;
            font-weight: 600;
            transition: all 0.2s ease;
            background: #fffdf7;
            color: #1c1c1c !important;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            background: #f7f3ff;
            border-color: #6e5aa3;
        }

        .primary-action .stButton > button {
            background: #cb89ff !important;
            border-color: #7a3f9f !important;
            color: #1f1030 !important;
            box-shadow: 0 10px 20px rgba(168, 109, 214, 0.26);
        }

        .primary-action .stButton > button:hover {
            background: #ebd4ff;
            border-color: #7c4f93;
        }

        .result-box {
            margin-top: 0.9rem;
            background: #f7f5ea;
            border: 1px solid rgba(13, 100, 86, 0.2);
            border-left: 6px solid var(--mint);
            border-radius: 14px;
            padding: 1rem 1rem;
            color: #1e1e1c;
        }

        .mode-title {
            font-size: 1.02rem;
            font-weight: 600;
            margin: 0.2rem 0 0.8rem;
        }

        @keyframes revealUp {
            from {
                opacity: 0;
                transform: translateY(18px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px;
            border: 1px solid rgba(18, 18, 18, 0.08);
            background: rgba(249, 249, 239, 0.85);
            box-shadow: 0 8px 24px rgba(40, 40, 40, 0.06);
            animation: revealUp 0.65s ease-out both;
            margin-bottom: 0.8rem;
        }

        @supports (animation-timeline: view()) {
            [data-testid="stVerticalBlockBorderWrapper"] {
                animation: revealUp linear both;
                animation-timeline: view();
                animation-range: entry 10% cover 35%;
            }
        }

        [data-testid="stSidebar"] .stRadio > div {
            gap: 0.35rem;
        }

        [data-testid="stSidebar"] .stRadio label {
            background: #ffffff;
            border: 1px solid rgba(13, 100, 86, 0.15);
            border-radius: 12px;
            padding: 0.45rem 0.55rem;
            width: 100%;
        }

        .auth-user-chip {
            display: inline-block;
            padding: 0.34rem 0.68rem;
            border-radius: 999px;
            border: 1px solid rgba(122, 63, 159, 0.35);
            background: #f4e8ff;
            color: #4d2369;
            font-size: 0.82rem;
            margin-bottom: 0.55rem;
        }

        .footer-wrap {
            margin-top: 1.2rem;
            padding: 1rem 1rem 0.65rem;
            border-top: 1px solid rgba(13, 100, 86, 0.2);
            color: #3f3f3f;
        }

        .footer-wrap h4 {
            margin: 0 0 0.45rem;
            font-size: 1.05rem;
        }

        .footer-copy {
            margin-top: 0.6rem;
            color: #6a6a6a;
            font-size: 0.82rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_data_uri = image_to_data_uri(LOGO_PATH)
if logo_data_uri:
    st.markdown(
        f"""
        <style>
            [data-testid="stAppViewContainer"] {{
                background-image:
                    radial-gradient(circle at 10% 10%, #f3f4e8 10%, #eeefde 36%, #e8e8d8 100%),
                    linear-gradient(rgba(238, 239, 222, 0.92), rgba(238, 239, 222, 0.92));
                background-size: cover, cover;
                background-repeat: no-repeat, no-repeat;
                background-position: center, center;
                
            }}

            [data-testid="stAppViewContainer"]::before {{
                background-image: url("{logo_data_uri}");
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "subtitle_segments" not in st.session_state:
    st.session_state.subtitle_segments = []
if "processed_url" not in st.session_state:
    st.session_state.processed_url = ""
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""
if "last_summary" not in st.session_state:
    st.session_state.last_summary = ""
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "auth_view" not in st.session_state:
    st.session_state.auth_view = ""

init_auth_db()


st.markdown(
    """
    <div class='top-banner'>
        <div class='top-nav'>
            <div class='top-nav-left'>
                <span class='top-nav-brand'>Watch-Wise.ai</span>
                <span class='top-nav-links'>Pricing</span>
                <span class='top-nav-links'>Help</span>
                <span class='top-nav-links'>Resources</span>
            </div>
            <div class='top-nav-links'>AI Video Understanding Platform</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

auth_left, auth_right = st.columns([4.6, 1.9], gap="small")
with auth_right:
    if st.session_state.is_logged_in:
        st.markdown(
            f"<div class='auth-shell'><span class='auth-user-chip'>{st.session_state.current_user}</span></div>",
            unsafe_allow_html=True,
        )
        if st.button("Logout", key="logout_btn_top"):
            st.session_state.is_logged_in = False
            st.session_state.current_user = ""
            st.session_state.auth_view = ""
            st.success("Logged out successfully.")
    else:
        login_col, signup_col = st.columns([1, 1.35])
        if login_col.button("Login", key="show_login_btn"):
            st.session_state.auth_view = "login"
        if signup_col.button("Sign up for free", key="show_signup_btn", type="primary"):
            st.session_state.auth_view = "signup"

auth_form_left, auth_form_right = st.columns([4.6, 1.9], gap="small")
with auth_form_right:
    if not st.session_state.is_logged_in and st.session_state.auth_view == "signup":
        with st.form("signup_form"):
            su_username = st.text_input("Username", key="signup_username")
            su_email = st.text_input("Email", key="signup_email")
            su_password = st.text_input("Password", type="password", key="signup_password")
            signup_submit = st.form_submit_button("Create Account")
        if signup_submit:
            ok, message = create_user(su_username.strip(), su_email.strip(), su_password)
            if ok:
                st.success(message)
                st.session_state.auth_view = "login"
            else:
                st.error(message)
    elif not st.session_state.is_logged_in and st.session_state.auth_view == "login":
        with st.form("login_form"):
            li_username = st.text_input("Username", key="login_username")
            li_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Login")
        if login_submit:
            ok, message = validate_login(li_username.strip(), li_password)
            if ok:
                st.session_state.is_logged_in = True
                st.session_state.current_user = li_username.strip()
                st.session_state.auth_view = ""
                st.success(message)
            else:
                st.error(message)

st.markdown( 
    """
    <section class="hero-wrap">
        <div class="hero-headline">
            <span class="soft">Don't watch,</span><span class="strong">ask the video</span>
        </div>
        <p class="hero-sub">
            Paste a YouTube link, generate a transcript, and get grounded answers from the video in seconds.
        </p>
        <p class="workflow-note">Workflow: Ingest video → Build vector index → Ask focused questions</p>
    </section>
    """,
    unsafe_allow_html=True,
)


left, right = st.columns([1.05, 1], gap="large")

with left:
    with st.container(border=True):
        st.markdown("<span class='status-chip'>Step 1 • Ingestion</span>", unsafe_allow_html=True)
        st.markdown("#### Video Source")
        url = st.text_input("Enter YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

        st.markdown("<div class='primary-action'>", unsafe_allow_html=True)
        process_clicked = st.button("Transcribe & Build Knowledge Base", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

        if process_clicked:
            if not url.strip():
                st.warning("Please enter a valid YouTube URL.")
            else:
                try:
                    with st.spinner("Downloading audio from YouTube..."):
                        audio_file = download_audio(url.strip())

                    with st.spinner("Transcribing speech to text..."):
                        transcript, subtitle_segments = transcribe(audio_file)

                    with st.spinner("Chunking transcript and building vector index..."):
                        chunks = chunk_text(transcript)
                        store = VectorStore()
                        store.build(chunks)

                    st.session_state.vector_store = store
                    st.session_state.transcript = transcript
                    st.session_state.subtitle_segments = subtitle_segments
                    st.session_state.processed_url = url.strip()

                    st.success("Video processed successfully. You can ask questions now.")
                except Exception as exc:
                    st.error(f"Processing failed: {exc}")
                finally:
                    if "audio_file" in locals() and os.path.exists(audio_file):
                        os.remove(audio_file)

with right:
    with st.container(border=True):
        st.markdown("<span class='status-chip'>Step 2 • Retrieval + Generation</span>", unsafe_allow_html=True)
        st.markdown("#### Ask About the Video")
        question = st.text_area("Your Question", placeholder="What are the key takeaways from this video?", height=118)
        enable_tts = st.toggle("Generate voice answer (TTS)")
        ask_clicked = st.button("Ask AI")

        if ask_clicked:
            if st.session_state.vector_store is None:
                st.warning("Please process a YouTube URL first.")
            elif not question.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    with st.spinner("Searching relevant transcript chunks..."):
                        context = st.session_state.vector_store.search(question.strip(), k=5)
                    with st.spinner("Generating answer with LLM..."):
                        answer = ask_llm(context, question.strip())

                    st.session_state.last_answer = answer

                    st.markdown(f"<div class='result-box'>{answer}</div>", unsafe_allow_html=True)

                    if enable_tts:
                        with st.spinner("Generating audio response..."):
                            audio_path = speak(answer)
                        st.audio(audio_path, format="audio/mp3")
                except Exception as exc:
                    st.error(f"Failed to answer: {exc}")

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("## WatchWise AI")
    st.markdown("### Dashboard")
    selected_mode = st.radio(
        "Studio Modes",
        options=[
            "AI - Ask anything about the video",
            "Get Transcript",
            "Play Video + Transcript",
            "Generate Summary",
            "Generate Closed Captions (CC)",
        ],
        label_visibility="collapsed",
    )

st.markdown("### Workspace")
with st.container(border=True):
    if selected_mode == "AI - Ask anything about the video":
        st.markdown("<p class='mode-title'>AI - Ask anything about the video</p>", unsafe_allow_html=True)
        if st.session_state.last_answer:
            st.markdown(f"<div class='result-box'>{st.session_state.last_answer}</div>", unsafe_allow_html=True)
        else:
            st.info("Ask a question from the right panel to see the answer here.")

    elif selected_mode == "Get Transcript":
        st.markdown("<p class='mode-title'>Get Transcript</p>", unsafe_allow_html=True)
        if st.session_state.transcript:
            st.text_area(
                "Transcript",
                st.session_state.transcript,
                height=360,
                key="transcript_full_view",
            )
            st.download_button(
                "Download Transcript (.txt)",
                data=st.session_state.transcript,
                file_name="transcript.txt",
                mime="text/plain",
            )
        else:
            st.warning("Process a YouTube video first to view transcript.")

    elif selected_mode == "Play Video + Transcript":
        st.markdown("<p class='mode-title'>Play Video + Transcript</p>", unsafe_allow_html=True)
        if st.session_state.processed_url:
            st.video(st.session_state.processed_url)
            if st.session_state.subtitle_segments:
                st.caption("Subtitle Timeline")
                st.dataframe(st.session_state.subtitle_segments, use_container_width=True, hide_index=True)
            else:
                st.info("No subtitle segments available yet.")
        else:
            st.warning("Process a YouTube URL first to enable video playback with transcript.")

    elif selected_mode == "Generate Summary":
        st.markdown("<p class='mode-title'>Generate Summary</p>", unsafe_allow_html=True)
        generate_summary = st.button("Generate Summary", key="generate_summary_btn")
        if generate_summary:
            if not st.session_state.transcript:
                st.warning("Process a YouTube video first.")
            else:
                try:
                    with st.spinner("Generating summary..."):
                        summary_chunks = chunk_text(st.session_state.transcript, chunk_size=350, overlap=70)[:10]
                        summary = ask_llm(
                            summary_chunks,
                            "Generate a clean, structured summary with key points and takeaways.",
                        )
                    st.session_state.last_summary = summary
                except Exception as exc:
                    st.error(f"Summary generation failed: {exc}")

        if st.session_state.last_summary:
            st.markdown(f"<div class='result-box'>{st.session_state.last_summary}</div>", unsafe_allow_html=True)

    elif selected_mode == "Generate Closed Captions (CC)":
        st.markdown("<p class='mode-title'>Generate Closed Captions (CC)</p>", unsafe_allow_html=True)
        if st.session_state.subtitle_segments:
            srt_content = build_srt(st.session_state.subtitle_segments)
            st.text_area("SRT Preview", srt_content, height=320, key="srt_preview_area")
            st.download_button(
                "Download Closed Captions (.srt)",
                data=srt_content,
                file_name="captions.srt",
                mime="application/x-subrip",
            )
        else:
            st.warning("Process a YouTube video first to generate closed captions.")

if st.session_state.transcript:
    with st.expander("Quick Transcript Preview", expanded=False):
        st.write(st.session_state.transcript[:1500])

if st.session_state.processed_url:
    st.caption(f"Indexed source: {st.session_state.processed_url}")

st.markdown(
    """
    <footer class="footer-wrap">
        <h4>Terms &amp; Services</h4>
        <p>
            This platform allows users to analyze YouTube videos using artificial intelligence.
            Users can generate transcripts, summaries, captions, and ask questions about video
            content. The service is intended for educational, research, and productivity purposes.
            Users are responsible for ensuring that their use complies with YouTube's terms of
            service and copyright policies. The platform does not store or redistribute video
            content but processes publicly available media for AI-based insights.
        </p>
        <p class="footer-copy">© 2026 Watch-Wise.AI – All rights reserved.</p>
    </footer>
    """,
    unsafe_allow_html=True,
)
