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

title_text = input("Enter Scholar Name: ")
caption_text = get_caption_text()
bottom_text_my = input("Enter bottom title: ")

destination_dir = os.path.join("capcut", sanitize_folder_name(bottom_text_my))
os.makedirs(destination_dir, exist_ok=True)

first_video_filename = os.path.basename(video_path)
new_video_path = os.path.join(destination_dir, first_video_filename)
shutil.move(video_path, new_video_path)

##################################
### NOW BURNING TEXT TO VIDEO
##################################

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


fixed_srt_path = os.path.abspath(os.path.join(destination_dir, f"{bottom_text_my.strip()}_fixed.srt"))
print(f"\n📄 Copied EMPTY SRT to: {fixed_srt_path}")

#print("📝 Opening subtitle file for manual editing...")
#subprocess.Popen(["notepad.exe", fixed_srt_path]).wait()
#input("\n✅ Done editing? Press ENTER to continue...")

os.startfile(destination_dir)
winsound.PlaySound("success.wav", winsound.SND_FILENAME)