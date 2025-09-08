#pip install nemo_toolkit[asr] pydub pysrt wtpsplit
 
import os
import time, winsound
import nemo.collections.asr as nemo_asr
from omegaconf import open_dict
from pydub import AudioSegment
from tqdm import tqdm

very_start = time.time()

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

# Step 2: Split into 3-minute chunks
def split_audio(input_audio_path, chunk_length_ms=15 * 1000):
    audio = AudioSegment.from_file(input_audio_path, format="mp3")
    chunks = []

    total_chunks = len(audio) // chunk_length_ms + (1 if len(audio) % chunk_length_ms else 0)

    for i in tqdm(range(0, len(audio), chunk_length_ms), desc="🔪 Splitting audio", unit="chunk", total=total_chunks):
        chunk = audio[i:i + chunk_length_ms]
        chunk = chunk.set_channels(1)

        os.makedirs("chunks_folder", exist_ok=True)  # Ensure output directory exists
        chunk_index = i // chunk_length_ms
        chunk_path = f"chunks_folder/chunk_{chunk_index}.mp3"

        chunk.export(chunk_path, format="mp3")
        chunks.append((chunk_path, i / 1000.0))  # Return chunk path and start time in seconds

    return chunks

# Step 3: Format time for SRT
def format_srt_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    return time.strftime('%H:%M:%S', time.gmtime(int(seconds))) + f",{ms:03d}"

# Step 4: Load model and configure decoding
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

# Step 5: Transcribe chunks and write combined SRT
def transcribe_chunks(model, chunks, output_srt_path):
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        subtitle_index = 1
        for chunk_path, chunk_start_sec in tqdm(chunks, desc="🔊 Transcribing chunks", unit="chunk"):
            #print(f"Transcribing {chunk_path} ...")
            hypotheses = model.transcribe([chunk_path], return_hypotheses=True)
            word_timestamps = hypotheses[0].timestamp['word']
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

import pysrt
from wtpsplit import SaT

MAX_DURATION_SECONDS = 12.0
THRESHHOLD = 0.05

def generate_sentence_srt_with_pysrt(input_srt_path, output_srt_path="sentence_level_max_time.srt"):
    # Step 1: Load word-level SRT
    subs = pysrt.open(input_srt_path, encoding="utf-8")

    # Step 2: Build full text and track word character spans
    full_text = ""
    spans = []  # List of (start_char_index, end_char_index)
    for sub in subs:
        start_idx = len(full_text)
        # Use strip() to remove leading/trailing whitespace, then add a single space
        word_text = sub.text.strip()
        if word_text:
            full_text += word_text + " "
            end_idx = len(full_text) - 1  # -1 to exclude the trailing space
            spans.append((start_idx, end_idx))

    # Step 3: Sentence segmentation
    sat = SaT("sat-12l-sm", language="ar", style_or_domain="general")
    sentences = sat.split(full_text, threshold=THRESHHOLD)

    sentence_subs = []
    
    # Track the last processed word index
    last_processed_word_idx = -1

    for sentence in sentences:
        sent_start = full_text.find(sentence.strip())
        if sent_start == -1:
            continue  # Skip if sentence not found in full_text

        sent_end = sent_start + len(sentence.strip())

        # Map to word-level indices
        first_word_idx = None
        last_word_idx = None
        for i, (s, e) in enumerate(spans):
            # A word is part of the sentence if its span is within or overlaps the sentence's span
            if s >= sent_start and first_word_idx is None:
                first_word_idx = i
            if e <= sent_end:
                last_word_idx = i
            
        # Ensure that word indices are valid and are not from a previously processed sentence
        if (
    first_word_idx is not None and 
    last_word_idx is not None and 
    first_word_idx <= last_word_idx and 
    first_word_idx > last_processed_word_idx
):
            word_indices = list(range(first_word_idx, last_word_idx + 1))
            current_chunk = []
            chunk_start_idx = word_indices[0]
            chunk_start_time = subs[chunk_start_idx].start

            for i in word_indices:
                current_chunk.append(i)
                chunk_end_time = subs[i].end
                duration = (chunk_end_time.ordinal - chunk_start_time.ordinal) / 1000.0

                is_last_word = i == word_indices[-1]
                if duration > MAX_DURATION_SECONDS or is_last_word:
                    # Create sub for the current chunk
                    text = ' '.join(subs[j].text.strip() for j in current_chunk)
                    sentence_subs.append(pysrt.SubRipItem(
                        index=len(sentence_subs) + 1,
                        start=chunk_start_time,
                        end=chunk_end_time,
                        text=text
                    ))
                    
                    # If duration exceeded, we might need to "rollback"
                    if duration > MAX_DURATION_SECONDS and len(current_chunk) > 1 and not is_last_word:
                        current_chunk = [current_chunk[-1]] # Start next chunk with the last word
                        chunk_start_time = subs[current_chunk[0]].start
                    else:
                        current_chunk = [] # Clear chunk for next sentence chunk
                    
            # Update the last processed word index to avoid re-processing words
            last_processed_word_idx = last_word_idx

    # Save final SRT
    new_srt = pysrt.SubRipFile(items=sentence_subs)
    new_srt.save(output_srt_path, encoding="utf-8")
    print(f"✅ Saved sentence-level SRT to: {output_srt_path}")

audio_input = "sharaf.mp3"
output_srt = "sharaf_SUB.srt"

print(f"MAKING CHUNKING...")
chunks = split_audio(audio_input)

print(f"LOADING MODEL")
asr_model = load_model()

print(f"TRANSCRIBING CHUNKS...")
transcribe_chunks(asr_model, chunks, output_srt)

get_time_lapsed(very_start)

print("Started SENTENCE SUBBING...")
final_sub_file = output_srt.split(".")[0] + "_sentenced.srt"
generate_sentence_srt_with_pysrt(input_srt_path=output_srt, output_srt_path=final_sub_file)

get_time_lapsed(very_start)
winsound.Beep(1000,500)