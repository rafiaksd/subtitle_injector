import os
import subprocess
from pytubefix import YouTube
import re
import tempfile
import winsound

def sanitize_filename(name):
    """Remove invalid filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_youtube_video(link, output_dir):
    """
    Download a YouTube video at user-selected quality.
    Handles both progressive and video-only streams.
    Returns the final output path and title.
    """
    yt = YouTube(link)
    title = sanitize_filename(yt.title)
    print(f"\n🎥 Title: {title}")

    # Collect available video streams
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
        raise ValueError("❌ No valid video streams found.")

    # Ask for quality selection
    index = int(input(f"\nSelect quality (1-{len(available_streams)}): "))
    if not (1 <= index <= len(available_streams)):
        raise ValueError("❌ Invalid selection.")

    selected_stream = available_streams[index - 1]

    # Define output paths
    base_video_path = os.path.join(output_dir, f"{title}_video.mp4")
    base_audio_path = os.path.join(output_dir, f"{title}_audio.m4a")
    final_output = os.path.join(output_dir, f"{title}.mp4")

    print("\n⬇️ Downloading video...")
    selected_stream.download(output_path=output_dir, filename=os.path.basename(base_video_path))

    # Handle non-progressive video
    if not selected_stream.is_progressive:
        print("🎧 Downloading audio...")
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        audio_stream.download(output_path=output_dir, filename=os.path.basename(base_audio_path))

        print("🔄 Merging video and audio...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", base_video_path,
            "-i", base_audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            final_output
        ], check=True, capture_output=True, text=True, encoding='utf-8')

        # Cleanup
        os.remove(base_video_path)
        os.remove(base_audio_path)
    else:
        # Progressive stream (already has audio)
        os.rename(base_video_path, final_output)

    print(f"✅ Final downloaded video saved at:\n{final_output}")
    winsound.PlaySound("downloaddone.wav", winsound.SND_FILENAME)

    return os.path.abspath(final_output), title

def clip_and_merge_youtube_video(link, time_ranges, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Download
    video_path, title = download_youtube_video(link, output_dir)

    # Step 2: Prepare temp folder
    temp_dir = tempfile.mkdtemp(prefix="clips_")
    clip_files = []

    # Step 3: Generate clips
    for i in range(0, len(time_ranges), 2):
        start = time_ranges[i]
        end = time_ranges[i+1]
        clip_path = os.path.join(temp_dir, f"clip_{i//2 + 1}.mp4")

        print(f"✂️ Trimming from {start} to {end}...")
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", start, "-to", end,
            "-i", video_path,
            "-c:v", "copy", "-c:a", "copy",
            clip_path
        ], check=True, capture_output=True, text=True)
        clip_files.append(clip_path)

    # Step 4: Create concat list file
    list_file = os.path.join(temp_dir, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")

    # Step 5: Merge clips
    final_output = os.path.join(output_dir, f"{title}_merged_clips.mp4")
    print("🔄 Merging all clips...")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        final_output
    ], check=True, capture_output=True, text=True)

    # Step 6: Cleanup
    for f in clip_files:
        os.remove(f)
    os.remove(video_path)

    winsound.PlaySound("downloaddone.wav", winsound.SND_FILENAME)
    print(f"✅ Final merged video saved at:\n{os.path.abspath(final_output)}")

    return os.path.abspath(final_output)

link = "https://youtu.be/z_nFaRbFRPU"
time_ranges = [
    "2:18", "3:01",
    "3:59", "4:13",
    "5:30", "6:10",
    "7:33", "7:50",
    "9:42", "10:46",
    "13:24", "13:41"
]

output_path = clip_and_merge_youtube_video(link, time_ranges)
print("🎉 Done:", output_path)