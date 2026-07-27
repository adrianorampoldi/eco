import os
from mistralai.client import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
model = "voxtral-mini-latest"

client = Mistral(api_key=api_key)

with open("./audio.mp3", "rb") as f:
   transcription_response = client.audio.transcriptions.complete(
       model=model,
       file={
           "content": f,
           "file_name": "audio.mp3",
       },diarize=True,
       timestamp_granularities=["segment"],
   )
transcription = "\n".join([f"[{s.start}s -> {s.end}s] {s.speaker_id} : {s.text}" for s in transcription_response.segments])
