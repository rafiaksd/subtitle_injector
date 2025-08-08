import cv2, subprocess, os, re, time, winsound

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

very_beginning = time.time()

# Global variables
drawing = False
ix, iy = -1, -1
ex, ey = -1, -1
rect_defined = False

to_burn_video_file = "clips/reading books of disbelievers.mp4"

# Main logic
def select_crop_area(video_path):
    # Mouse callback to draw rectangle
    def draw_rectangle(event, x, y, flags, param):
     global ix, iy, ex, ey, drawing, rect_defined

     if event == cv2.EVENT_LBUTTONDOWN:
          drawing = True
          ix, iy = x, y
          ex, ey = x, y

     elif event == cv2.EVENT_MOUSEMOVE and drawing:
          ex, ey = x, y
          rect_defined = True

     elif event == cv2.EVENT_LBUTTONUP:
          drawing = False
          ex, ey = x, y
          rect_defined = True

    global ix, iy, ex, ey, rect_defined

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_index = 0

    if not cap.isOpened():
        print("Error opening video.")
        return

    cv2.namedWindow("Video Crop Selector")
    cv2.setMouseCallback("Video Crop Selector", draw_rectangle)

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if not ret:
            print(f"[!] Could not read frame {frame_index}")
            break

        display_frame = frame.copy()

        # Draw rectangle
        if drawing:
          cv2.rectangle(display_frame, (ix, iy), (ex, ey), (0, 255, 0), 2)
        elif rect_defined:
          cv2.rectangle(display_frame, (ix, iy), (ex, ey), (0, 255, 0), 2)

        # Frame info text
        cv2.putText(display_frame, f"Frame {frame_index+1}/{total_frames}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Video Crop Selector", display_frame)

        key = cv2.waitKey(0)

        if key == ord('c') and rect_defined:
            # Confirm crop
            x1, y1 = min(ix, ex), min(iy, ey)
            x2, y2 = max(ix, ex), max(iy, ey)
            width = x2 - x1
            height = y2 - y1
            #print(f"\nSelected Crop Area:\nStart X: {x1}\nStart Y: {y1}\nWidth: {width}\nHeight: {height}")
            cv2.destroyAllWindows()
            return (x1,y1,width,height)
        elif key == ord('a'):
            frame_index = max(frame_index - 20, 0)
        elif key == ord('d'):
            frame_index = min(frame_index + 20, total_frames - 1)

    cap.release()
    cv2.destroyAllWindows()

print(f"👀 👀 SELECT CROP AREA 🧐 🧐 🛤️🛤️ ")
crop_x, crop_y, crop_w, crop_h = select_crop_area(to_burn_video_file)

hor_res = 1920
ver_res = 1080
cropped_vid_horizontal_width = 820

def overlay_video_on_bg(video_path, bg_path, crop_x, crop_y, crop_w, crop_h, 
                        output_path="output.mp4", temp_video="temp_noaudio.mp4"):
    
    final_resolution=(hor_res, ver_res)
    overlay_pos=(hor_res-cropped_vid_horizontal_width, 0) # x,y position where cropped video will be placed

    # Load background image and resize to final resolution
    bg = cv2.imread(bg_path)
    bg = cv2.resize(bg, final_resolution)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video FPS: {fps:.2f}, frames: {total_frames}, original size: {width}x{height}")

    # Prepare VideoWriter for output video (no audio yet)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_video, fourcc, fps, final_resolution)

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Crop selected region from frame
        cropped = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]

        # Resize cropped video to 600x1080
        cropped_resized = cv2.resize(cropped, (cropped_vid_horizontal_width, ver_res))

        # Prepare background copy for this frame
        frame_bg = bg.copy()

        # Overlay cropped video on background at overlay_pos
        x_offset, y_offset = overlay_pos
        frame_bg[y_offset:y_offset+ver_res, x_offset:x_offset+cropped_vid_horizontal_width] = cropped_resized

        out.write(frame_bg)
        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"Processed frame {frame_idx}/{total_frames}")

    cap.release()
    out.release()
    print("Video without audio written:", temp_video)

    # Use ffmpeg to copy original audio to new video
    cmd = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i", temp_video,
        "-i", video_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    print("Merging audio with video using ffmpeg...")
    subprocess.run(cmd, check=True,capture_output=True, text=True, encoding='utf-8')
    print("Final video with audio saved as:", output_path)

    # Cleanup temp video
    os.remove(temp_video)

    return output_path

cropped_vid_burned = "burned_videos/test_burning_vert_vid.mp4"

overlay_video_on_bg(
    video_path=to_burn_video_file,
    bg_path="bg.png",
    crop_x=crop_x, crop_y=crop_y, crop_w=crop_w, crop_h=crop_h,
    output_path=cropped_vid_burned
)

###################
### FINAL BURN ####
###################
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
            parts[19] = '3' # MarginL 
            parts[20] = '180' # MarginR
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

def burn_subtitles_with_title(bg_video: str, ass_path: str, output_path: str, top_text: str, bottom_text: str, logo_image: str, subtitle_below_top: str):
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
        f"x=(1100-text_w)/2:"
        f"y=20,"

        #add dua text
        f"drawtext="
        f"text='{subtitle_below_top}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':"
        f"fontcolor=yellow:"
        f"fontsize=72:"
        f"x=(1100-text_w)/2:"
        f"y=80," 
        
        f"drawtext="
        f"text='{bottom_text}':"
        f"fontfile='C\\:/Windows/Fonts/calibrib.ttf':"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(1100-text_w)/2:"
        f"y=h-text_h-40,"
        
        f"subtitles='{ass_path}'[bg_vid_with_text];"

        # Step 3: Overlay the logo in top-right corner of the processed background
        f"[bg_vid_with_text][logo_scaled]overlay=W-w-20:20,scale=1920:1080"
    )

    # Run FFmpeg command
    subprocess.run([
        'ffmpeg',
        '-i', bg_video,       # Input 0: Background image
        '-i', logo_image,     # Input 1: Logo, # Input 2: Video (unused in overlay, just for timing/audio)
        '-filter_complex', filter_complex,
        '-shortest',
        '-y',                 # Overwrite output
        output_path
    ], check=True, capture_output=True, text=True, encoding='utf-8') #capture_output=True, text=True
    print("✅✅ Subtitle BURNING SUCCESSFUL")

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
        ], check=True, capture_output=True, text=True, encoding='utf-8') #capture_output=True, text=True,
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

title_text = "Sheikh Mansoor as Samaari"
caption_text = "حفظه الله"
bottom_text_my = "Reading Disbelievers Books to Refute Them"

srt_file = "fixedsubs/reading books of disbelievers_translation_fixed.srt"
bg_video = cropped_vid_burned

#constant INPUT 
my_logo = "logo.png"
final_video_name = bottom_text_my.strip()
ending_video = "ending.mp4"

#intermediate files
ass_file = "subtitleTEST.ass"
intermediate_output = "intermediate_output.mp4"

os.makedirs("burned_videos", exist_ok=True) # Ensure the 'subs/' directory exists
final_output = os.path.join("burned_videos", f"{final_video_name}.mp4")

convert_srt_to_ass(srt_file, ass_file)
modify_ass_to_center(ass_file)
add_fade_animation_to_ass(ass_file, fade_out_ms=100)
burn_subtitles_with_title(bg_video=bg_video, ass_path=ass_file, output_path=intermediate_output, top_text=title_text, bottom_text=bottom_text_my, logo_image=my_logo, subtitle_below_top=caption_text)
concatenate_videos(intermediate_output, ending_video, final_output)

# Cleanup (optional)
os.remove(ass_file)
os.remove(intermediate_output)
os.remove(cropped_vid_burned)
print("✅ Cleanup done.")

#open the burned_videos folder
os.startfile(final_output) #play the video
folder_path = os.path.abspath("burned_videos")
os.startfile(folder_path) #for windows

print("✅ COMPLETE")
get_time_lapsed(very_beginning, emojis="🏁🏁🏁")

winsound.PlaySound("success.wav", winsound.SND_FILENAME)