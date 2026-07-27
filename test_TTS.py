import base64
import numpy as np
import sounddevice as sd
from queue import Queue
from mistralai.client import Mistral
import os


api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)
voice_id = "gb_jane_neutral"


audio_queue = Queue(maxsize=100)


def audio_callback(outdata, frames, time, status):
   """Callback for audio playback."""
   try:
       data = audio_queue.get_nowait()
   except:
       outdata.fill(0)
       return
   outdata[:len(data), 0] = data
   if len(data) < len(outdata):
       outdata[len(data):, 0] = 0


def play_audio(text: str) -> None:
   """Stream and play audio for the given text."""
   with sd.OutputStream(
       samplerate=24000,
       channels=1,
       dtype=np.float32,
       callback=audio_callback,
       blocksize=960,
       latency="low",
   ):
       with client.audio.speech.complete(
           model="voxtral-mini-tts-2603",
           input=text,
           voice_id=voice_id,
           response_format="pcm",
           stream=True,
       ) as stream:
           for event in stream:
               if event.event == "speech.audio.delta":
                   audio_data = base64.b64decode(event.data.audio_data)
                   audio_array = np.frombuffer(audio_data, dtype=np.float32)
                   for i in range(0, len(audio_array), 960):
                       block = audio_array[i:i + 960]
                       audio_queue.put(block)
               elif event.event == "speech.audio.done":
                   break


       # Wait for the queue to empty
       while not audio_queue.empty():
           sd.sleep(100)

testo="Pietro Paleocapa (1788-1869) è stato un ingegnere, matematico e politico italiano, noto soprattutto per il suo contributo allo sviluppo delle infrastrutture idrauliche e ferroviarie nel Regno Lombardo-Veneto e poi nel Regno d’Italia. È considerato uno dei padri dell’ingegneria idraulica italiana."
play_audio(testo)

