#!pip install numpy==2.0.0 nemo_toolkit[asr]

import nemo.collections.asr as nemo_asr
import time

print("🔃🔃 Loading model...")
asr_model = nemo_asr.models.ASRModel.from_pretrained("hishab/titu_stt_bn_fastconformer") #nvidia/parakeet-tdt-0.6b-v2 hishab/titu_stt_bn_fastconformer
print(f"✅✅ Loaded ASR model ")


def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")


def transcribe(audio_path: str):
    print("📜📜 Started transcribing...")

    transcriptions = asr_model.transcribe([audio_path])
    transcription_text = transcriptions[0]

    return transcription_text
    
audio_file = "bengali_test_compressed.mp3"

start_time = time.time()

transcription = transcribe(audio_file)
print()
print(transcription)

get_time_lapsed(start_time)