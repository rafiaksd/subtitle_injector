import subprocess, winsound
import cv2

# Global variables
drawing = False
ix, iy = -1, -1
ex, ey = -1, -1
rect_defined = False

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

my_video_path = "clips/rect_affairs_medium.mp4"
crop_x, crop_y, crop_w, crop_h = select_crop_area(my_video_path)

hor_res = 1920
ver_res = 1080
cropped_vid_horizontal_width = 720

def get_video_duration(video_path):
    """Returns video duration in seconds using ffprobe."""
    result = subprocess.run([
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ], capture_output=True, text=True)

    return float(result.stdout.strip())

def overlay_and_concatenate(video_path, bg_path, crop_x, crop_y, crop_w, crop_h, ending_video_path, logo_path, output_path):
    video_duration = get_video_duration(video_path)

    filter_complex = (
        # Crop and scale main video
        f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={cropped_vid_horizontal_width}:{ver_res},setsar=1[cropped];"
        # Scale background
        f"[1:v]scale={hor_res}:{ver_res},setsar=1[bg];"
        # Overlay cropped video on background
        f"[bg][cropped]overlay={hor_res - cropped_vid_horizontal_width}:0[overlaid];"
        #scale logo
        f"[3:v]scale=180:180[logo_scaled];"
        # Overlay logo on top right of previous overlay
        f"[overlaid][logo_scaled]overlay=x=main_w-w-30:y=30[with_logo];"
        # Reset timestamps for overlay + audio streams
        f"[with_logo]setpts=PTS-STARTPTS[v0];"
        f"[0:a]asetpts=PTS-STARTPTS[a0];"
        f"[2:v]setpts=PTS-STARTPTS,scale={hor_res}:{ver_res},setsar=1[v1];"
        f"[2:a]asetpts=PTS-STARTPTS[a1];"
        # Concatenate video+audio streams
        f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-loop", "1", "-t", str(video_duration), "-i", bg_path,
        "-i", ending_video_path,
        "-i", logo_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        output_path
    ]

    print("Running ffmpeg with combined overlay + concat + logo...")
    subprocess.run(cmd, check=True)
    print(f"Output saved to {output_path}")

overlay_and_concatenate(my_video_path, "bg.png", crop_x, crop_y, crop_w, crop_h, "ending.mp4" , "logo.png" , "testing_vert_burn_onego.mp4")
winsound.Beep(1000,500)