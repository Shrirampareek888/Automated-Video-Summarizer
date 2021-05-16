import speech_recognition as sr
from os import path
from pydub import AudioSegment
import ffprobe

# convert mp3 file to wav                                                       
sound = AudioSegment.from_mp3("/home/tejas/Projects/EDI-2/Flask/static/notes.mp3")
sound.export("notes.wav", format="wav")


# transcribe audio file                                                         
AUDIO_FILE = "notes.wav"

# use the audio file as the audio source                                        
r = sr.Recognizer()
with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)  # read the entire audio file                  

        print("Transcription: " + r.recognize_google(audio))