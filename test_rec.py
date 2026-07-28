# record from mic and save to audio.mp3
import sounddevice as sd
import soundfile as sf
import numpy as np
import keyboard
import threading
import queue
import time
import sys

samplerate = 44100
channels = 1
filename = "test.mp3"

frames = queue.Queue()
recording = threading.Event()

def audio_callback(indata, frames_count, time_info, status):
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
    sf.write(filename, audio_data, samplerate)
    print(f"Saved recording to {filename}")

def toggle_record(event):
    if recording.is_set():
        print("Stopping recording...")
        recording.clear()
        save_audio()
    else:
        print("Starting recording...")
        while not frames.empty():
            frames.get()
        recording.set()

keyboard.on_press_key('r', toggle_record)

print("Press 'r' to start/stop recording. Exit with Ctrl+C.")

with sd.InputStream(callback=audio_callback, channels=channels, samplerate=samplerate):
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        if recording.is_set():
            recording.clear()
            save_audio()
        print("Exited.")

