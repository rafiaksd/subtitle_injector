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

input_file = "fearingfuture.mp4"
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
subtitle_start = time.time()
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

get_time_lapsed(subtitle_start, "📕📕")
print(f"Word-level subtitles saved to {output_sub_file}")
winsound.Beep(1000, 500)
