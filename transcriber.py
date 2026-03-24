import yt_dlp
from faster_whisper import WhisperModel
import uuid


# download youtube audio
def download_audio(url):

    output = f"audio_{uuid.uuid4()}.mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output,
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output


# speech to text
def transcribe(audio_file):

    model = WhisperModel("base", compute_type="int8")

    segments, info = model.transcribe(audio_file)

    transcript = ""
    subtitle_segments = []

    for segment in segments:

        transcript += segment.text + " "

        subtitle_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })

    return transcript, subtitle_segments