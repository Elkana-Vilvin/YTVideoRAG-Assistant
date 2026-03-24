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

- LLM: Ollama (Llama 3 / 3B model)
- Speech-to-Text: Faster-Whisper
- Embeddings: Sentence Transformers (MiniLM)
- Vector DB: FAISS
- Framework: Streamlit
- Video Processing: yt-dlp
- TTS: gTTS

Architecture 

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

