from faster_whisper import WhisperModel
import os, time, winsound
import srt
import datetime

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

model_size = "turbo"

# Load Whisper model (e.g., "large-v3" or "turbo")
model = WhisperModel(model_size, device="cpu", compute_type="int8")

input_file = "clips/short_a_audio.mp4"
input_file_name = input_file.split(".")[0]

print("Started WORD LEVEL Transcribing...")
word_start = time.time()

segments, info = model.transcribe(
    input_file, 
    word_timestamps=True,
    beam_size=5,
    vad_filter=True
)

# Collect words with timestamps
words_with_timestamps = []
for segment in segments:
    for word in segment.words:
        words_with_timestamps.append(word)
get_time_lapsed(word_start, "🔤")

# Convert each word into a separate .srt entry
subtitle_entries = []
for i, word in enumerate(words_with_timestamps):
    start = datetime.timedelta(seconds=word.start)
    end = datetime.timedelta(seconds=word.end)
    text = word.word.strip()
    if not text:
        continue
    subtitle_entries.append(srt.Subtitle(index=i + 1, start=start, end=end, content=text))

# Save to .srt file
output_sub_file = input_file_name + ".srt"
with open(output_sub_file, "w", encoding="utf-8") as f:
    f.write(srt.compose(subtitle_entries))

print(f"Word-level subtitles saved to {output_sub_file}")
winsound.Beep(1000, 500)

import pysrt
from wtpsplit import SaT

MAX_DURATION_SECONDS = 8.0

def generate_sentence_srt_with_pysrt(input_srt_path, output_srt_path="sentence_level_max_time.srt", threshold=0.05):
    # Step 1: Load word-level SRT
    subs = pysrt.open(input_srt_path, encoding="utf-8")

    # Step 2: Build full text and track word character spans
    full_text = ""
    spans = []  # List of (start_char_index, end_char_index)
    for sub in subs:
        start_idx = len(full_text)
        full_text += sub.text.strip() + " "
        end_idx = len(full_text)
        spans.append((start_idx, end_idx))

    # Step 3: Sentence segmentation
    sat = SaT("sat-12l-sm", language="ar", style_or_domain="general")
    sentences = sat.split(full_text, threshold=threshold)

    sentence_subs = []
    for sentence in sentences:
        sent_start = full_text.find(sentence)
        sent_end = sent_start + len(sentence)

        # Map to word-level indices
        first_word_idx = None
        last_word_idx = None
        for i, (s, e) in enumerate(spans):
            if s >= sent_start and first_word_idx is None:
                first_word_idx = i
            if e <= sent_end:
                last_word_idx = i

        if first_word_idx is not None and last_word_idx is not None:
            word_indices = list(range(first_word_idx, last_word_idx + 1))
            current_chunk = []
            chunk_start_idx = word_indices[0]
            chunk_start_time = subs[chunk_start_idx].start

            for i in word_indices:
                current_chunk.append(i)
                chunk_end_time = subs[i].end
                duration = (chunk_end_time.ordinal - chunk_start_time.ordinal) / 1000.0

                # If the chunk exceeds 8 seconds or this is the last word
                is_last_word = i == word_indices[-1]
                if duration > MAX_DURATION_SECONDS or is_last_word:
                    if duration > MAX_DURATION_SECONDS and len(current_chunk) > 1:
                        # Remove last word and process current_chunk
                        last = current_chunk.pop()
                        i -= 1  # Step back to reprocess last word
                        chunk_end_time = subs[current_chunk[-1]].end
                        is_last_word = False  # still more to go
                    else:
                        last = None  # nothing to reprocess

                    text = ' '.join(subs[j].text.strip() for j in current_chunk)
                    sentence_subs.append(pysrt.SubRipItem(
                        index=len(sentence_subs) + 1,
                        start=chunk_start_time,
                        end=chunk_end_time,
                        text=text
                    ))

                    # Prepare for next chunk
                    if last is not None:
                        current_chunk = [last]
                        chunk_start_time = subs[last].start
                    else:
                        current_chunk = []
                        if not is_last_word:
                            chunk_start_time = subs[i + 1].start

    # Save final SRT
    new_srt = pysrt.SubRipFile(items=sentence_subs)
    new_srt.save(output_srt_path, encoding="utf-8")
    print(f"✅ Saved sentence-level SRT to: {output_srt_path}")

print("Started SENTENCE SUBBING...")
final_sub_file = input_file_name + "_sentenced.srt"
generate_sentence_srt_with_pysrt(input_srt_path=output_sub_file, output_srt_path=final_sub_file)
get_time_lapsed(word_start, "🏁🏁")