 
import os
import time, winsound, subprocess
import nemo.collections.asr as nemo_asr
from omegaconf import open_dict
from pydub import AudioSegment
from tqdm import tqdm

word_transcription_start = time.time()

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

def split_audio(input_audio_path, chunk_length_ms=15 * 1000):
    audio = AudioSegment.from_file(input_audio_path, format="mp3")
    chunks = []

    total_chunks = len(audio) // chunk_length_ms + (1 if len(audio) % chunk_length_ms else 0)

    for i in tqdm(range(0, len(audio), chunk_length_ms), desc="🔪 Splitting audio", unit="chunk", total=total_chunks):
        chunk = audio[i:i + chunk_length_ms]

        os.makedirs("chunks_folder", exist_ok=True)  # Ensure output directory exists
        chunk_index = i // chunk_length_ms
        chunk_path = f"chunks_folder/chunk_{chunk_index}.mp3"

        # Convert chunk to mono before exporting
        chunk = chunk.set_channels(1)

        chunk.export(chunk_path, format="mp3")
        chunks.append((chunk_path, i / 1000.0))  # Return chunk path and start time in seconds

    return chunks

def format_srt_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    return time.strftime('%H:%M:%S', time.gmtime(int(seconds))) + f",{ms:03d}"

def load_model():
    print("Loading ASR model...")
    model = nemo_asr.models.ASRModel.from_pretrained("nvidia/stt_ar_fastconformer_hybrid_large_pcd_v1.0")
    decoding_cfg = model.cfg.decoding
    with open_dict(decoding_cfg):
        decoding_cfg.preserve_alignments = True
        decoding_cfg.compute_timestamps = True
        decoding_cfg.segment_separators = ["?", "!", "."]
        decoding_cfg.word_separator = " "
    model.change_decoding_strategy(decoding_cfg)
    return model

def transcribe_chunks(model, chunks, output_srt_path):
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        subtitle_index = 1
        for chunk_path, chunk_start_sec in tqdm(chunks, desc="🔊 Transcribing chunks", unit="chunk"):
            #print(f"Transcribing {chunk_path} ...")
            hypotheses = model.transcribe([chunk_path], return_hypotheses=True)

            
            word_timestamps = hypotheses[0]
            time_stride = 8 * model.cfg.preprocessor.window_stride

            for stamp in word_timestamps:
                start_sec = stamp['start_offset'] * time_stride + chunk_start_sec
                end_sec = stamp['end_offset'] * time_stride + chunk_start_sec
                word = stamp.get('word', stamp.get('char'))

                srt_file.write(f"{subtitle_index}\n")
                srt_file.write(f"{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n")
                srt_file.write(f"{word}\n\n")
                subtitle_index += 1

            os.remove(chunk_path)  # clean up chunk file

    print(f"SRT file saved as {output_srt_path} ✅")

#audio_input = convert_mp4_to_mp3(input_file)
#print(f"CONVERTED 📷📷 MP4 to 🔉🔉 MP3")

output_srt = "testing_ar_nemo.srt"

print(f"MAKING CHUNKING...")
chunks = split_audio("sharaf.mp3")

print(f"LOADING MODEL")
asr_model = load_model()

print(f"TRANSCRIBING CHUNKS...")
transcribe_chunks(asr_model, chunks, output_srt)

get_time_lapsed(word_transcription_start)
winsound.Beep(1000,500)