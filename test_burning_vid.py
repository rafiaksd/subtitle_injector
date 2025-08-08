import subprocess, re, os, time

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

abs_time_start = time.time()

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
            parts[2] = '24' #fontsize
            parts[7] = '1' #bold:1, default:-1
            #parts[13] = '3' # horizontal spacing
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

def burn_subtitles_with_title(bg_image: str, video_input: str, ass_path: str, output_path: str, top_text: str, bottom_text: str, logo_image: str, subtitle_below_top: str):
    print(f"Starting BURNING SUBTITLE...")
    # Define the filter complex
    filter_complex = (
        # Step 1: Scale the logo first
        f"[1:v]scale=180:180[logo_scaled];"

        # Step 2: Draw title and speaker name on background image, and burn in subtitles
        f"[0:v]drawtext="
        f"text='{top_text}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':"
        f"fontcolor=yellow:"
        f"fontsize=72:"
        f"x=(w-text_w)/2:"
        f"y=20,"

        #add dua text
        f"drawtext="
        f"text='{subtitle_below_top}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':"
        f"fontcolor=yellow:"
        f"fontsize=72:"
        f"x=(w-text_w)/2:"
        f"y=80," 
        
        f"drawtext="
        f"text='{bottom_text}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(w-text_w)/2:"
        f"y=h-text_h-40,"
        
        f"subtitles='{ass_path}'[bg_with_text];"

        # Step 3: Overlay the logo in top-right corner of the processed background
        f"[bg_with_text][logo_scaled]overlay=W-w-20:20,scale=1920:1080"
    )

    # Run FFmpeg command
    subprocess.run([
        'ffmpeg',
        '-loop', '1',
        '-i', bg_image,       # Input 0: Background image
        '-i', logo_image,     # Input 1: Logo
        '-i', video_input,    # Input 2: Video (unused in overlay, just for timing/audio)
        '-filter_complex', filter_complex,
        '-shortest',
        '-y',                 # Overwrite output
        output_path
    ], check=True, capture_output=True, text=True, encoding='utf-8') #capture_output=True, text=True

def concatenate_videos(video_1: str, video_2: str, output_path: str):
    try:
        subprocess.run([
            'ffmpeg',
            '-i', video_1,
            '-i', video_2,
            '-filter_complex',
            (
                # Normalize first video (video_1)
                "[0:v]setsar=1[v0];"
                # Normalize second video (video_2)
                "[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                "setsar=1[v1];"
                # Audio passthrough or normalize audio sample rate (optional)
                "[0:a]aresample=async=1[a0];"
                "[1:a]aresample=async=1[a1];"
                # Concatenate videos
                "[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]"
            ),
            '-map', '[outv]',
            '-map', '[outa]',
            '-y',
            output_path
        ], check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"✅ Concatenation successful → {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Concatenation failed:\n{e.stderr}")
        raise

def get_caption_text():
    while True:
        choice = input("Enter 0 for HafidhahuAllah, 1 for RahimahuAllah: ").strip()
        if choice == "0":
            return "حفظه الله"
        elif choice == "1":
            return "رحمه الله"
        else:
            print("❌ Invalid input. Please enter 0 or 1.")

import shutil

os.makedirs("fixedsubs", exist_ok=True)
base_filename = os.path.splitext(os.path.basename("clips/think_good_short.mp4"))[0]

title_text = "Sheikh Mansoor"
caption_text = "حفظه الله"
bottom_text_my = "BEING YAY Content CURRENT State"

video_file = "clips/think_good_short.mp4"
base_filename = os.path.splitext(os.path.basename(video_file))[0]

srt_file = "fixedsubs/think_good_short_translation_fixed.srt"

#constant INPUT
bg_image = "bg.png" 
my_logo = "logo.png"
ending_video = "ending.mp4"
final_video_name = "gonnaTESTVidFULL"

#intermediate files
ass_file = "subtitleTEST.ass"
intermediate_output = "intermediate_output.mp4"

os.makedirs("burned_videos", exist_ok=True) # Ensure the 'subs/' directory exists
final_output = os.path.join("burned_videos", f"{final_video_name}.mp4")

convert_srt_to_ass(srt_file, ass_file)
modify_ass_to_center(ass_file)
add_fade_animation_to_ass(ass_file, fade_out_ms=100)
burn_subtitles_with_title(bg_image=bg_image, video_input=video_file, ass_path=ass_file, output_path=final_output, top_text=title_text, bottom_text=bottom_text_my, logo_image=my_logo, subtitle_below_top=caption_text)

os.startfile(final_output)

get_time_lapsed(abs_time_start)