import subprocess
import os, time
import tkinter as tk
from tkinter import filedialog
import re, winsound
from pytubefix import YouTube

#new branch test

# https://www.youtube.com/watch?v=BZP1rYjoBgI the 30 second video 
trim = input("✂️ Do you want to trim the video? (yes/no): ").strip().lower()

if trim=="yes":
    start = input("⏱️ Start time (e.g. 00:00:05): ").strip()
    end = input("⏱️ End time (e.g. 00:01:00): ").strip()

# Folder setup
FULL_DIR = os.path.abspath("full_videos")
CLIP_DIR = os.path.abspath("clips")
os.makedirs(FULL_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)

very_beginning = time.time()

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

def sanitize_for_ffmpeg(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("%", "%%")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n").replace("\r", "")
    text = text.replace("'", "\\'")
    return text

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

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
        winsound.PlaySound("downloaddone.wav", winsound.SND_FILENAME)

        final_output = os.path.abspath(final_output)

        # === Ask if trim is needed
        
        if trim == "yes":
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

            #delete_full_video = input("👀👀 Do you want to DELETE the FULL video? (yes/no): ").strip().lower()
            delete_full_video = "yes"
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

video_path = get_video_from_youtube()
print(f"\n✅ Final usable video path: {video_path}")

if trim=="yes":
    os.startfile(CLIP_DIR)
else:
     os.startfile(FULL_DIR)
