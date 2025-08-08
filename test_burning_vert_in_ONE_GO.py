def overlay_and_concatenate(video_path, bg_path, crop_x, crop_y, crop_w, crop_h, ending_video_path, output_path):
    # Construct filter_complex string
    filter_complex = (
        f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
        f"scale={cropped_vid_horizontal_width}:{ver_res}[cropped];"
        f"[1:v]scale={hor_res}:{ver_res}[bg];"
        f"[bg][cropped]overlay={hor_res - cropped_vid_horizontal_width}:0[overlaid];"
        f"[overlaid]setpts=PTS-STARTPTS[v0];"
        f"[0:a]asetpts=PTS-STARTPTS[a0];"
        f"[2:v]setpts=PTS-STARTPTS[v1];"
        f"[2:a]asetpts=PTS-STARTPTS[a1];"
        f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]"
    )
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-loop", "1", "-i", bg_path,
        "-i", ending_video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        output_path
    ]
    
    print("Running ffmpeg with combined overlay + concat...")
    subprocess.run(cmd, check=True)
    print(f"Output saved to {output_path}")
