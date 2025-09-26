from faster_whisper import WhisperModel
import os
import time
import srt
import datetime
import winsound

# Define the Whisper model size and initialize the model
model_size = "large-v3-turbo"  # You can choose "large-v3" or "turbo" for faster results
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# Path to your video/audio file
video_path = "jap_audio_two.mp4"  # Replace with the actual file path
input_file_name = video_path.split(".")[0]  # Get the base name without extension

print("Started Transcribing...")  # Simplified message
word_start = time.time()

# Transcribe the audio/video without word-level timestamps
segments, info = model.transcribe(
    video_path,
    word_timestamps=False,  # Disable word-level timestamps
    beam_size=5,  # Increase for better accuracy, decrease for speed
    vad_filter=True  # Voice activity detection to remove silence
)

# Print the full transcription (segment-level only)
print("\nFull Transcription:")
full_transcription = ""
for segment in segments:
    full_transcription += segment.text + " "  # Combine all segment texts into one
    print(segment.text)  # Print each segment's transcription

# Generate subtitles (SRT file format)
subtitles = []
for segment in segments:
    start_time = str(datetime.timedelta(seconds=segment.start))
    end_time = str(datetime.timedelta(seconds=segment.end))
    subtitle_text = segment.text

    subtitle = srt.Subtitle(
        index=len(subtitles) + 1,
        start=datetime.timedelta(seconds=segment.start),
        end=datetime.timedelta(seconds=segment.end),
        content=subtitle_text
    )
    subtitles.append(subtitle)

# Save subtitles to a .srt file
srt_file_name = input_file_name + ".srt"
with open(srt_file_name, "w") as f:
    f.write(srt.compose(subtitles))

print(f"\nTranscription complete. Subtitles saved to {srt_file_name}")

word_end = time.time()
print(f"Total transcription time: {word_end - word_start:.2f} seconds")

# Play a beep sound to indicate completion
winsound.Beep(1000, 500)
