import subprocess, time, os

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

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

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
        choice = "0"
        if choice == "0":
            return "حفظه الله"
        elif choice == "1":
            return "رحمه الله"
        else:
            print("❌ Invalid input. Please enter 0 or 1.")

title_text = "test scholar"
caption_text = get_caption_text()
bottom_text_my = "testing horz direct concat"

video_file = "clips/think_good_short.mp4"
base_filename = os.path.splitext(os.path.basename(video_file))[0]

srt_file = "fixedsubs_ar/think_good_short_sentenced.srt"

#constant INPUT
bg_image = "bg.png" 
my_logo = "logo.png"
ending_video = "ending.mp4"
final_video_name = "horz_direct_concat.mp4"

ass_file = "subtitle.ass"

started_converstion = time.time()

convert_srt_to_ass(srt_file, ass_file)
modify_ass_to_center(ass_file)
burn_subtitles_with_title(bg_image=bg_image, video_input=video_file, ass_path=ass_file, output_path=final_video_name, top_text=title_text, bottom_text=bottom_text_my, logo_image=my_logo, subtitle_below_top=caption_text, ending_video=ending_video)

get_time_lapsed(started_converstion)

os.startfile(final_video_name)