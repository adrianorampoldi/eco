from mistralai.client import Mistral
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import keyboard
import threading
import queue
import time
import sys
from sympy import true
import base64
import numpy as np
import os

api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

websearch_agent = client.beta.agents.create(
   model="mistral-small-latest",
   description="Agent able to search information over the web, such as news, weather, sport results...",
   name="Websearch Agent",
   instructions="You are a general assistant. You have the ability to perform web searches with `web_search` to find up-to-date information. Keep your replies concise and to the point, with no markdown or code blocks.",
   tools=[{"type": "web_search"}],
   completion_args={
       "temperature": 0.3,
       "top_p": 0.95,
   }
)

# record from mic and save to audio.mp3
samplerate = 44100
channels = 1
audio_file = "audio.mp3"

frames = queue.Queue()
recording = threading.Event()
enable_record = 0

def rec_callback(indata, frames_count, time_info, status):
    if status:
        print(status, file=sys.stderr)
    if recording.is_set():
        frames.put(indata.copy())

def save_audio():
    chunks = []
    while not frames.empty():
        chunks.append(frames.get())
    if not chunks:
        print("No audio recorded.")
        return
    audio_data = np.concatenate(chunks, axis=0)
    sf.write(audio_file, audio_data, samplerate)
    print(f"Saved recording to {audio_file}")
    global enable_record
    enable_record = 0

def toggle_record():
    if recording.is_set():
        print("Stopping recording...")
        recording.clear()
        save_audio()
    else:
        print("Starting recording...")
        while not frames.empty():
            frames.get()
        recording.set()

def record():
    #handler = keyboard.on_press_key('ctrl+r', toggle_record)
    handler = keyboard.add_hotkey('r', toggle_record)
    print("Press 'R' to start/stop recording.")
    global enable_record
    enable_record = 1
    
    with sd.InputStream(callback=rec_callback, channels=channels, samplerate=samplerate):
        try:
            while enable_record==1:
                time.sleep(0.1)
        except KeyboardInterrupt:
            if recording.is_set():
                recording.clear()
                save_audio()

    #keyboard.unhook(handler)
    keyboard.remove_hotkey(handler)
    print("Recording terminated.")
    

def stt(audio_file):
    model = "voxtral-mini-latest"
    with open(audio_file, "rb") as f:
        transcription_response = client.audio.transcriptions.complete(
        model=model,
        file={
            "content": f,
            "file_name": audio_file,
            },
        diarize=True,
        timestamp_granularities=["segment"]
    )
    transcription = "\n".join([f"[{s.start}s -> {s.end}s] {s.speaker_id} : {s.text}" for s in transcription_response.segments])
    #print("Transcription:\n", transcription)
    return transcription

voice_id = "gb_jane_neutral"
audio_queue =  queue.Queue(maxsize=100)

def play_callback(outdata, frames, time, status):
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
       callback=play_callback,
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

conversation_id = None
user_message=""
while true:
   # record user
   record()
   # STT user audio
   #user_message = input("User: ")
   user_message = stt(audio_file)
   print(user_message)
   if user_message.lower().find("quit") != -1:
      break
   if conversation_id:
       response = client.beta.conversations.append(
           conversation_id=conversation_id,
           inputs=user_message
       )
   else:
       response = client.beta.conversations.start(
           agent_id=websearch_agent.id,
           inputs=user_message
       )
   conversation_id = response.conversation_id
   content = response.outputs[-1].content
   if isinstance(content, list):
       content = ".".join([c.text for c in content])
   print("Agent:", content)
   play_audio(content)
keyboard.flush()