# YTVideoRAG-Assistant
🎥🧠 AskTube AI is an AI-powered assistant that lets you interact with YouTube videos like never before.

Ask questions, generate summaries, extract transcripts, and even create closed captions — all powered by a local LLM + RAG pipeline.

🔹 Ask anything about a YouTube video (RAG-based Q&A)
🔹 Generate full transcript using speech-to-text
🔹 Play video with transcript
🔹 AI-powered video summary
🔹 Generate Closed Captions (.srt)
🔹 Chat-style interface (like ChatGPT)
🔹 Works locally using Ollama (no API cost)

- LLM: Ollama (Llama 3 / 3B model) can use better model based on the machine we use
- Speech-to-Text: Faster-Whisper
- Embeddings: Sentence Transformers (MiniLM)
- Vector DB: FAISS
- Framework: Streamlit
- Video Processing: yt-dlp
- TTS: gTTS

# Architecture 

YouTube URL
   ↓
Audio Extraction (yt-dlp)
   ↓
Speech-to-Text (Whisper)
   ↓
Chunking
   ↓
Embeddings (Bi-Encoder)
   ↓
FAISS Vector DB
   ↓
User Query → Retrieval
   ↓
LLM (Ollama)
   ↓
Answer / Summary / Captions

# Setup cmds

python3 -m venv venv
 
source venv/bin/activate
 
pip install --upgrade pip
pip install streamlit yt-dlp faster-whisper faiss-cpu sentence-transformers ollama gTTS

#New terminal
ollama serve
 
ollama pull llama3
 
streamlit run app.py
