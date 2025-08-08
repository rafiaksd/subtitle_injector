import os, subprocess, re, time
from pytubefix import YouTube

def sanitize_filename(name):
    # Remove illegal characters for file names
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_youtube_video():
    absolute_start_time = time.time()
    link = input("Enter the YouTube video URL: ")
    if not link:
        print("❌ No link provided.")
        return

    try:
        yt = YouTube(link)
        print(f"\n🎥 Video Title: {yt.title}")
        title = sanitize_filename(yt.title)
        
        # List all video streams (.mp4) including video-only and progressive
        streams = yt.streams.filter(file_extension='mp4', type='video').order_by('resolution').desc()
        available_streams = []
        qualities_seen = set()

        print("\n📺 Available Video Qualities:")
        for i, stream in enumerate(streams):
            quality = stream.resolution
            is_progressive = "Progressive" if stream.is_progressive else "Video-only"
            if quality and quality not in qualities_seen:
                qualities_seen.add(quality)
                available_streams.append(stream)
                print(f"{len(available_streams)}. {quality} ({is_progressive})")

        if not available_streams:
            print("❌ No downloadable video streams found.")
            return

        selected_index = int(input(f"Select Quality: (1-{len(available_streams)}): "))
        if not selected_index or not (1 <= selected_index <= len(available_streams)):
            print("❌ Invalid selection.")
            return

        selected_stream = available_streams[selected_index - 1]
        save_path = r"C:\Users\hadar\Downloads\free download manager"
        os.makedirs(save_path, exist_ok=True)

        video_file = os.path.join(save_path, f"{title}_video.mp4")
        selected_stream.download(output_path=save_path, filename=os.path.basename(video_file))
        print(f"\nVideo downloaded: {video_file}")

        if not selected_stream.is_progressive:
            print("⚠️ Video-only stream detected. Downloading audio...")

            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            audio_ext = audio_stream.mime_type.split('/')[1]
            audio_file = os.path.join(save_path, f"{title}_audio.{audio_ext}")
            audio_stream.download(output_path=save_path, filename=os.path.basename(audio_file))
            print(f"Audio downloaded: {audio_file}")

            # Final merged output
            final_output = os.path.join(save_path, f"{title}.mp4")

            merge_time_start = time.time()
            print("🔄 Merging video and audio...")

            # Use proper quoting and codec for MP4 container
            merge_cmd = [
                "ffmpeg", "-y",
                "-i", video_file,
                "-i", audio_file,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                final_output
            ]

            result = subprocess.run(merge_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            if result.returncode == 0:
                conversion_time_took = time.time() - merge_time_start
                absolute_time_took = time.time() - absolute_start_time

                os.remove(video_file)
                os.remove(audio_file)
                print(f"\n⏰ Conversion time: {conversion_time_took:.1f} s  | ⏰ Total Time: {absolute_time_took:.1f} s")
                print(f"✅ Final video with audio saved at: {final_output}")
            else:
                print("❌ FFmpeg merge failed:")
                print(result.stderr)
        else:
            print("✅ The video already contains audio (progressive stream). No merging needed.")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    download_youtube_video()
