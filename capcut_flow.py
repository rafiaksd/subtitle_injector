##################
### check GPU ####
##################

#import torch

#if not torch.cuda.is_available():
    #raise EnvironmentError("🚫 GPU runtime not detected! Please enable it: Runtime > Change runtime type > Hardware accelerator: T4 GPU")

#!pip install pytubefix srt faster_whisper wtpsplit pysrt

import os, re, time, subprocess, winsound, shutil
from pytubefix import YouTube
import tkinter as tk
from tkinter import filedialog
#!pip install pytubefix srt faster_whisper wtpsplit pysrt

##################################
### DOWNLOAD / LOAD VIDEO
##################################

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

def sanitize_folder_name(name: str, replacement: str = "_") -> str:
    # Define a list of characters that are illegal on most systems
    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized = re.sub(illegal_chars, replacement, name)
    sanitized = sanitized.rstrip(". ")
    sanitized = sanitized.lstrip()

    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if sanitized.upper() in reserved_names:
        sanitized = f"{sanitized}_safe"

    return sanitized

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

        winsound.Beep(1000,500)
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

winsound.Beep(1000,500)

def get_caption_text():
    while True:
        choice = input("Enter 0 for HafidhahuAllah, 1 for RahimahuAllah: ").strip()
        if choice == "0":
            return "حفظه الله"
        elif choice == "1":
            return "رحمه الله"
        else:
            print("❌ Invalid input. Please enter 0 or 1.")

#title_text = input("Enter Scholar Name: ")
#caption_text = get_caption_text()
bottom_text_my = input("Enter bottom title: ")

destination_dir = os.path.join("capcut", sanitize_folder_name(bottom_text_my))
os.makedirs(destination_dir, exist_ok=True)

first_video_filename = os.path.basename(video_path)
new_video_path = os.path.join(destination_dir, first_video_filename)
shutil.move(video_path, new_video_path)

##################################
### TRANSCRIBE & SEMANTIC
##################################

##################################
### GENERATE WORD LEVEL SUBTITLES
##################################

print(f"Continuing to Generate WORD LEVEL Timestamps")
word_transcription_start = time.time()

input_file = new_video_path
input_file_name = input_file.split(".")[0]

os.makedirs("subs", exist_ok=True)

base_filename = os.path.basename(input_file_name)  # e.g., "The 30-Second Video"
base_filename = os.path.splitext(base_filename)[0]  # remove .mp4 or any extension

output_sub_file = os.path.join("subs", base_filename + ".srt")

print("Started WORD LEVEL Transcribing...")

#pip install nemo_toolkit[asr] pydub pysrt wtpsplit
 
import os
import time, winsound
import nemo.collections.asr as nemo_asr
from omegaconf import open_dict
from pydub import AudioSegment
from tqdm import tqdm

def split_audio(input_audio_path, chunk_length_ms=15 * 1000):
    audio = AudioSegment.from_file(input_audio_path, format="mp4")
    chunks = []

    total_chunks = len(audio) // chunk_length_ms + (1 if len(audio) % chunk_length_ms else 0)

    for i in tqdm(range(0, len(audio), chunk_length_ms), desc="✂️✂️ Splitting audio", unit="chunk", total=total_chunks):
        chunk = audio[i:i + chunk_length_ms]
        chunk = chunk.set_channels(1)
        
        os.makedirs("chunks_folder", exist_ok=True)  # Ensure output directory exists
        chunk_index = i // chunk_length_ms
        chunk_path = f"chunks_folder/chunk_{chunk_index}.mp3"

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

output_srt = output_sub_file

print(f"MAKING CHUNKING...")
chunks = split_audio(input_file)

print(f"LOADING MODEL")
asr_model = load_model()

print(f"TRANSCRIBING CHUNKS...")
transcribe_chunks(asr_model, chunks, output_srt)

get_time_lapsed(word_transcription_start)
winsound.Beep(1000,500)

print(f"Word-level subtitles saved to {output_sub_file}")

##################################
### Generate Semantic Sentence ###
##################################

import pysrt
from wtpsplit import SaT

MAX_DURATION_SECONDS = 16.0
THRESHOLD = 0.25

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

    # Fix end times to match next subtitle's start time
    for i in range(len(sentence_subs) - 1):
        sentence_subs[i].end = sentence_subs[i + 1].start
    print(f"⏭️ Changed SUB end time = next subtitles start time")

    # Merge subtitles shorter than MIN_DURATION_SECONDS with the previous one
    MIN_DURATION_SECONDS = 3  # Minimum readable subtitle duration in seconds
    i = 1  # Start from second subtitle
    while i < len(sentence_subs):
        duration = (sentence_subs[i].end.ordinal - sentence_subs[i].start.ordinal) / 1000.0
        if duration < MIN_DURATION_SECONDS:
            # Merge with previous
            prev = sentence_subs[i - 1]
            current = sentence_subs[i]

            prev.text = prev.text.strip() + "... " + current.text.strip()
            prev.end = current.end

            sentence_subs.pop(i)
        else:
            i += 1
    print(f"🤝🤝 Merged sub less than {MIN_DURATION_SECONDS} seconds with previous sub")

    # Save final SRT
    new_srt = pysrt.SubRipFile(items=sentence_subs)
    new_srt.save(output_srt_path, encoding="utf-8")
    print(f"✅ Saved sentence-level SRT to: {output_srt_path}")
    get_time_lapsed(semantic_sub_start_time, "🆎 🆎")
    winsound.Beep(1000,500)

print("Started SENTENCE SUBBING...")
semantic_ar_sub_file = "fixedsubs_ar/" + base_filename + "_sentenced.srt"
generate_sentence_srt_with_pysrt(input_srt_path=output_sub_file, output_srt_path=semantic_ar_sub_file)

fixed_srt_path = os.path.abspath(os.path.join("fixedsubs", f"{base_filename}_fixed.srt"))
shutil.copyfile(semantic_ar_sub_file, fixed_srt_path)
print(f"\n📄 Copied original SRT to: {fixed_srt_path}")

##################################
#### TRANSLATION #################
##################################

##################################
### DONE, NOW COPY TO FOLDER #####
##################################

semantic_ar_sub_file = fixed_srt_path
print("SELECTED SUB to COPY for FIXING...")

# arabic sentenced file
fixed_srt_path = os.path.abspath(os.path.join(destination_dir, f"AR_{bottom_text_my.strip()}.srt"))
shutil.copyfile(semantic_ar_sub_file, fixed_srt_path)
print(f"\n📄 Copied SEMANTIC ARABIC SRT to: {fixed_srt_path}")

# to translate file
fixed_srt_path = os.path.abspath(os.path.join(destination_dir, f"TO_ENG_{bottom_text_my.strip()}.srt"))
shutil.copyfile(semantic_ar_sub_file, fixed_srt_path)
print(f"\n📄 Copied TO TRANSLATE FILE to: {fixed_srt_path}")

#translation
#fixed_srt_path = os.path.abspath(os.path.join(destination_dir, f"{bottom_text_my.strip()}.srt"))
#shutil.copyfile(translated_eng_sub, fixed_srt_path)
#print(f"\n📄 Copied ENG SRT to: {fixed_srt_path}")

os.startfile(destination_dir)
winsound.PlaySound("victory.wav", winsound.SND_FILENAME)

##################################
### NOW BURNING TEXT TO VIDEO
##################################

"""
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

def burn_subtitles_with_title( bg_image, video_input, output_path, top_text, bottom_text, logo_image, subtitle_below_top, ending_video):
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
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=h-text_h-40[bg_with_text];"
        #f"subtitles='{ass_path}'[bg_with_text];"

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

video_file = new_video_path
base_filename = os.path.splitext(os.path.basename(video_file))[0]

#constant INPUT
bg_image = "bg.png" 
my_logo = "logo.png"
ending_video = "ending.mp4"
final_video_name = bottom_text_my.strip()

os.makedirs("burned_videos", exist_ok=True) # Ensure the 'subs/' directory exists
final_output = os.path.join("burned_videos", f"{final_video_name}.mp4")

started_converstion = time.time()

burn_subtitles_with_title(bg_image=bg_image, video_input=video_file, output_path=final_output, top_text=title_text, bottom_text=bottom_text_my, logo_image=my_logo, subtitle_below_top=caption_text, ending_video=ending_video)

get_time_lapsed(started_converstion)
print("✅ TEXT burned to center of the video with logo in top-right corner.")

video_to_move = final_output

# Get new full path
video_filename = os.path.basename(video_to_move)
new_video_path = os.path.join(destination_dir, video_filename)

shutil.move(video_to_move, new_video_path)

print(f"\n✅ Final usable video path: {new_video_path}")
winsound.PlaySound("victory.wav", winsound.SND_FILENAME)
"""