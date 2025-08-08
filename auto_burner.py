import subprocess,os,time,winsound,re

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
            parts[7] = '1' #bold:1, default:-1
            parts[16] = '0' # outline thickness
            parts[18] = '5'  # Alignment field
            parts[19] = '70' # MarginL
            parts[20] = '70' # MarginR
            line = ','.join(parts) + '\n'
            style_section_found = False

        modified_lines.append(line)

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    print("✅ Centering SUBTITLE subtitle.ass DONE")

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

video_path = "C:/Users/hadar/Desktop/Laravel Tuts/Projects/ai integration/auto subtitle injector/clips/handhala.mp4"

os.makedirs("fixedsubs", exist_ok=True)
base_filename = os.path.splitext(os.path.basename(video_path))[0]

original_srt_path = "fixedsubs/داء الغفلة الشيخ عبد الرزاق البدر_00_22_16_to_00_35_38_translation_fixed.srt"
fixed_srt_path = os.path.abspath(os.path.join("fixedsubs", f"{base_filename}_translation_fixed.srt"))

# Step 1: Copy original SRT to fixed location as a starting point
shutil.copyfile(original_srt_path, fixed_srt_path)
print(f"\n📄 Copied original SRT to: {fixed_srt_path}")

# Step 2: Open the fixed SRT file in Notepad (or your preferred editor)
print("📝 Opening subtitle file for manual editing...")
subprocess.Popen(["notepad.exe", fixed_srt_path]).wait()

# Step 3: Wait for user confirmation
input("\n✅ Done editing? Press ENTER to continue...")

# Step 4: Validate file exists
if not os.path.exists(fixed_srt_path):
    print("❌ Fixed subtitle file not found! Please ensure it's saved and try again.")
    exit(1)

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
intermediate_output = "intermediate_output.mp4"

os.makedirs("burned_videos", exist_ok=True) # Ensure the 'subs/' directory exists
final_output = os.path.join("burned_videos", f"{final_video_name}_subbed.mp4")

started_converstion = time.time()

convert_srt_to_ass(srt_file, ass_file)
modify_ass_to_center(ass_file)
add_fade_animation_to_ass(ass_file, fade_out_ms=100)
burn_subtitles_with_title(bg_image=bg_image, video_input=video_file, ass_path=ass_file, output_path=intermediate_output, top_text=title_text, bottom_text=bottom_text_my, logo_image=my_logo, subtitle_below_top=caption_text)
concatenate_videos(intermediate_output, ending_video, final_output)

get_time_lapsed(started_converstion)
print("✅ Done: Subtitles burned to center of the video with logo in top-right corner.")

# Cleanup (optional)
os.remove(ass_file)
os.remove(intermediate_output)
print("✅ Cleanup done.")

#open the burned_videos folder
folder_path = os.path.abspath("burned_videos")
os.startfile(folder_path) #for windows

winsound.PlaySound("success.wav", winsound.SND_FILENAME)