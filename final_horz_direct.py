import subprocess
import os, time
import tkinter as tk
from tkinter import filedialog
import re
from pytubefix import YouTube

very_beginning = time.time()

# Folder setup
FULL_DIR = os.path.abspath("full_videos")
CLIP_DIR = os.path.abspath("clips")
os.makedirs(FULL_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# https://www.youtube.com/watch?v=BZP1rYjoBgI the 30 second video 
def get_video_from_youtube():
    link = input("Enter the YouTube video URL: ").strip()
    if not link:
        print("❌ No link provided.")
        return None

    try:
        yt = YouTube(link)
        title = sanitize_filename(yt.title)
        print(f"\n🎥 Title: {title}")

        streams = yt.streams.filter(file_extension='mp4', type='video').order_by('resolution').desc()
        available_streams = []
        seen_res = set()

        print("\n📺 Available Video Qualities:")
        for stream in streams:
            res = stream.resolution
            if res and res not in seen_res:
                seen_res.add(res)
                available_streams.append(stream)
                tag = "Progressive" if stream.is_progressive else "Video-only"
                print(f"{len(available_streams)}. {res} ({tag})")

        if not available_streams:
            print("❌ No valid video streams found.")
            return None

        index = int(input(f"Select quality (1-{len(available_streams)}): "))
        if not (1 <= index <= len(available_streams)):
            print("❌ Invalid selection.")
            return None

        selected_stream = available_streams[index - 1]
        base_video_path = os.path.join(FULL_DIR, f"{title}_video.mp4")
        base_audio_path = os.path.join(FULL_DIR, f"{title}_audio.m4a")
        final_output = os.path.join(FULL_DIR, f"{title}.mp4")

        print("⬇️ Downloading video...")
        selected_stream.download(output_path=FULL_DIR, filename=os.path.basename(base_video_path))

        if not selected_stream.is_progressive:
            print("🎧 Downloading audio...")
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            audio_stream.download(output_path=FULL_DIR, filename=os.path.basename(base_audio_path))

            print("🔄 Merging video and audio...")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", base_video_path,
                "-i", base_audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                final_output
            ], check=True,capture_output=True, text=True, encoding='utf-8')

            os.remove(base_video_path)
            os.remove(base_audio_path)
        else:
            # Progressive video has audio — rename directly
            os.rename(base_video_path, final_output)

        print(f"✅ Final downloaded video saved at:\n{final_output}")
        final_output = os.path.abspath(final_output)

        # === Ask if trim is needed
        trim = input("✂️ Do you want to trim the video? (yes/no): ").strip().lower()
        if trim == "yes":
            start = input("⏱️ Start time (e.g. 00:00:05): ").strip()
            end = input("⏱️ End time (e.g. 00:01:00): ").strip()

            # Make times filename-safe
            start_safe = start.replace(":", "_")
            end_safe = end.replace(":", "_")

            trimmed_filename = f"{title}_{start_safe}_to_{end_safe}.mp4"
            trimmed_path = os.path.join(CLIP_DIR, trimmed_filename)

            subprocess.run([
                "ffmpeg", "-ss", start, "-to", end,
                "-i", final_output,
                "-c:v", "copy", "-c:a", "copy",
                "-y", trimmed_path
            ], check=True,capture_output=True, text=True, encoding='utf-8')

            delete_full_video = input("👀👀 Do you want to DELETE the FULL video? (yes/no): ").strip().lower()
            if delete_full_video == "yes":
                os.remove(final_output)
            else:
                print(f"💯💯 Full video - {final_output} - not deleted")
            final_output = os.path.abspath(trimmed_path)
            print(f"✂️ Trimmed video saved at:\n{final_output}")


        print(f"YOUTUBE VIDEO WORK FINISHED, FINAL OUTPUT: ")
        print(f"{final_output}")
     
        return final_output

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

CLIP_DIR = os.path.abspath("clips")
os.makedirs(CLIP_DIR, exist_ok=True)

def get_video_from_local():
    root = tk.Tk()
    root.withdraw()
    root.update() #make sure tkinter is ready
    root.attributes('-topmost', True)  # Force it to be on top

    file_path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video files", "*.mp4 *.mkv *.mov *.webm *.avi *.flv"), ("All files", "*.*")]
    )

    if not file_path:
        print("❌ No file selected.")
        return None

    abs_path = os.path.abspath(file_path)
    base_name = os.path.basename(abs_path)
    base_name_no_ext = os.path.splitext(base_name)[0]

    trim = input("✂️ Do you want to trim the video? (yes/no): ").strip().lower()
    if trim == "yes":
        start = input("⏱️ Start time (e.g. 00:00:05): ").strip()
        end = input("⏱️ End time (e.g. 00:01:00): ").strip()

        # Clean timestamps for filename
        start_safe = start.replace(":", "-")
        end_safe = end.replace(":", "-")
        trimmed_name = f"{base_name_no_ext}_{start_safe}_to_{end_safe}.mp4"
        trimmed_path = os.path.join(CLIP_DIR, trimmed_name)

        subprocess.run([
            'ffmpeg', '-ss', start, '-to', end,
            '-i', abs_path,
            '-c:v', 'copy', '-c:a', 'copy',
            '-y', trimmed_path
        ], check=True, capture_output=True, text=True, encoding='utf-8')

        delete_original = input("🗑️ Delete full original video to save space? (yes/no): ").strip().lower()
        if delete_original == "yes" and os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                print(f"🗑️ Deleted original video: {abs_path}")
            except Exception as e:
                print(f"❌ Could not delete original video:\n{e}")

        abs_path = os.path.abspath(trimmed_path)

    print(f"\n✅ LOCAL VIDEO FILE READY:\n{abs_path}")
    return abs_path


print("Choose source:")
print("1. YouTube")
print("2. Local file")

choice = input("Enter 1 or 2: ").strip()

if choice == "1":
     video_path = get_video_from_youtube()
elif choice == "2":
     video_path = get_video_from_local()
else:
     print("❌ Invalid choice.")
     exit()

print(f"\n✅ Final usable video path: {video_path}")

##################################
### GENERATE WORD LEVEL SUBTITLES
##################################

print(f"Continuing to Generate WORD LEVEL Timestamps")

from faster_whisper import WhisperModel
import os, time, winsound
import srt
import datetime

model_size = "turbo"

# Load Whisper model (e.g., "large-v3" or "turbo")
model = WhisperModel(model_size, device="cpu", compute_type="int8")

input_file = video_path
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

# Ensure the 'subs/' directory exists
os.makedirs("subs", exist_ok=True)

# Get only the base filename without path
base_filename = os.path.basename(input_file_name)  # e.g., "The 30-Second Video"

# Remove extension if present
base_filename = os.path.splitext(base_filename)[0]  # remove .mp4 or any extension

# Build valid output path
output_sub_file = os.path.join("subs", base_filename + ".srt")

with open(output_sub_file, "w", encoding="utf-8") as f:
    f.write(srt.compose(subtitle_entries))

print(f"Word-level subtitles saved to {output_sub_file}")
winsound.Beep(1000, 500)

import shutil

os.makedirs("fixedsubs", exist_ok=True)
base_filename = os.path.splitext(os.path.basename(video_path))[0]

original_srt_path = output_sub_file

##################################
### Generate Semantic Sentence ###
##################################

import pysrt
from wtpsplit import SaT

MAX_DURATION_SECONDS = 8.0
THRESHOLD = 0.15

def generate_sentence_srt_with_pysrt(input_srt_path, output_srt_path, threshold=THRESHOLD):
    # Step 1: Load word-level SRT
    semantic_sub_start_time = time.time()
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
    get_time_lapsed(semantic_sub_start_time, "🆎 🆎")

print("Started SENTENCE SUBBING...")
semantic_ar_sub_file = "fixedsubs_ar/" + base_filename + "_sentenced.srt"
generate_sentence_srt_with_pysrt(input_srt_path=original_srt_path, output_srt_path=semantic_ar_sub_file)

fixed_srt_path = os.path.abspath(os.path.join("fixedsubs", f"{base_filename}_fixed.srt"))
shutil.copyfile(semantic_ar_sub_file, fixed_srt_path)
print(f"\n📄 Copied original SRT to: {fixed_srt_path}")

print("📝 Opening subtitle file for manual editing...")
subprocess.Popen(["notepad.exe", fixed_srt_path]).wait()

input("\n✅ Done editing? Press ENTER to continue...")

if not os.path.exists(fixed_srt_path):
    print("❌ Fixed subtitle file not found! Please ensure it's saved and try again.")
    exit(1)

##################################
### NOW BURNING SUB TO VIDEO
##################################

def convert_srt_to_ass(srt_path: str, ass_path: str):
    subprocess.run([
        'ffmpeg',
        '-i', srt_path,
        ass_path, '-y'
    ], check=True, capture_output=True, text=True, encoding='utf-8')

    print("✅ Converted .srt to .ass file")

def modify_ass_to_center(ass_path: str):
    print(f"Now modifying to center, for subtitle.ass file")
    with open(ass_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_lines = []
    style_section_found = False

    for line in lines:
        if line.strip().startswith("[V4+ Styles]"):
            style_section_found = True
        elif style_section_found and line.startswith("Style:"):
            parts = line.strip().split(',')
            parts[1] = 'Calibri Bold'
            parts[2] = '24'
            parts[7] = '1' #bold:1, default:-1
            parts[16] = '0' # outline thickness
            parts[18] = '5'  # Alignment field
            parts[19] = parts[20] = '70' # MarginL, MarginR
            line = ','.join(parts) + '\n'
            style_section_found = False

        modified_lines.append(line)

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    print("✅ Centering SUBTITLE subtitle.ass DONE")

def add_fade_animation_to_ass(file_path, fade_out_ms=100):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("Dialogue:"):
            # Extract the style override block (starts with { ... })
            match = re.match(r"(Dialogue:[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,)(\{.*?\})?(.*)", line)
            if match:
                prefix, tag_block, text = match.groups()
                tag_block = tag_block or ""
                if "\\fad" not in tag_block and "\\fade" not in tag_block:
                    # Add fade-out if not already present
                    tag_block = tag_block.rstrip("}") + f"\\fad(0,{fade_out_ms})" + "}" if tag_block else f"{{\\fad(0,{fade_out_ms})}}"
                new_line = prefix + tag_block + text
                new_lines.append(new_line + "\n")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

     #override the same subtitle .ass file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def get_video_duration(video_path):
    result = subprocess.run([
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ], capture_output=True, text=True )
    return float(result.stdout.strip())


def burn_subtitles_with_title( bg_image, video_input, ass_path, output_path, top_text, bottom_text, logo_image, subtitle_below_top, ending_video):
    print("🚀 Starting burning subtitles and concatenation...")

    # Step 1: Get main video duration
    duration = get_video_duration(video_input)

    # Step 2: Build filter_complex
    drawtext_filter = (
        # Scale background and add texts
        f"[0:v]scale=1920:1080,"
        f"drawtext=text='{top_text}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':fontcolor=yellow:fontsize=72:x=(w-text_w)/2:y=20,"
        f"drawtext=text='{subtitle_below_top}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':fontcolor=yellow:fontsize=72:x=(w-text_w)/2:y=100,"
        f"drawtext=text='{bottom_text}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=h-text_h-40,"
        f"subtitles='{ass_path}'[bg_with_text];"

        # Scale logo
        f"[2:v]scale=180:-1[logo_scaled];"

        # Overlay logo
        f"[bg_with_text][logo_scaled]overlay=W-w-20:20[with_logo];"

        # Set timestamps and concat both videos
        f"[with_logo]setsar=1,setpts=PTS-STARTPTS[v0];"
        f"[1:a]asetpts=PTS-STARTPTS[a0];"
        f"[3:v]scale=1920:1080,setsar=1,setpts=PTS-STARTPTS[v1];"
        f"[3:a]asetpts=PTS-STARTPTS[a1];"

        # Concatenate processed main + ending
        f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]"
    )

    # Step 3: Full FFmpeg command with 4 inputs
    cmd = [
        "ffmpeg",
        "-loop", "1", "-t", str(duration), "-i", bg_image,  # [0:v]
        "-i", video_input,                                 # [1:a]
        "-i", logo_image,                                  # [2:v]
        "-i", ending_video,                                # [3:v][3:a]
        "-filter_complex", drawtext_filter,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-y",
        output_path
    ]

    subprocess.run(cmd, check=True)
    print(f"✅ Final video with subtitles and ending created: {output_path}")

def get_caption_text():
    while True:
        choice = input("Enter 0 for HafidhahuAllah, 1 for RahimahuAllah: ").strip()
        if choice == "0":
            return "حفظه الله"
        elif choice == "1":
            return "رحمه الله"
        else:
            print("❌ Invalid input. Please enter 0 or 1.")

title_text = input("Enter Scholar Name: ")
caption_text = get_caption_text()
bottom_text_my = input("Enter bottom title: ")

video_file = video_path
base_filename = os.path.splitext(os.path.basename(video_file))[0]

srt_file = fixed_srt_path

#constant INPUT
bg_image = "bg.png" 
my_logo = "logo.png"
ending_video = "ending.mp4"
final_video_name = bottom_text_my.strip()

#intermediate files
ass_file = "subtitle.ass"

os.makedirs("burned_videos", exist_ok=True) # Ensure the 'subs/' directory exists
final_output = os.path.join("burned_videos", f"{final_video_name}.mp4")

started_converstion = time.time()

convert_srt_to_ass(srt_file, ass_file)
modify_ass_to_center(ass_file)
add_fade_animation_to_ass(ass_file, fade_out_ms=100)
burn_subtitles_with_title(bg_image=bg_image, video_input=video_file, ass_path=ass_file, output_path=final_output, top_text=title_text, bottom_text=bottom_text_my, logo_image=my_logo, subtitle_below_top=caption_text, ending_video=ending_video)

get_time_lapsed(started_converstion)
print("✅ Done: Subtitles burned to center of the video with logo in top-right corner.")

# Cleanup (optional)
os.remove(ass_file)
print("✅ Cleanup done.")

#open the burned_videos folder
os.startfile(final_output) #play the video
folder_path = os.path.abspath("burned_videos")
os.startfile(folder_path) #for windows

print("✅ COMPLETE")
get_time_lapsed(very_beginning, emojis="🏁🏁🏁")

winsound.PlaySound("success.wav", winsound.SND_FILENAME)