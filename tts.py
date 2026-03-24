from gtts import gTTS


def speak(text, filename="answer.mp3"):

    tts = gTTS(text)

    tts.save(filename)

    return filename