import subprocess

video_file = "testing_vert_burn_onego.mp4"
subtitle_file = "test_sub.ass"  # Use .ass for best compatibility

try:
    subprocess.run(["C:/Program Files/Aegisub/Aegisub.exe", subtitle_file, video_file])
except FileNotFoundError:
    print("Aegisub not found. Please ensure it's installed and in your system's PATH.")