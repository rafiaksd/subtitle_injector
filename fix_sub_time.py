import pysrt

def adjust_sub_end_times(input_srt_path, output_srt_path):
    # Load subtitles
    subs = pysrt.open(input_srt_path, encoding="utf-8")

    # Adjust end times so each ends at the start of the next (except the last)
    for i in range(len(subs) - 1):
        subs[i].end = subs[i + 1].start

    # Save the modified subtitles
    subs.save(output_srt_path, encoding="utf-8")
    print(f"✅ Saved adjusted SRT to: {output_srt_path}")

# Example usage:
input_path = "eng.srt"     # Replace with your actual input filename
output_path = "wealth_matter_fixed.srt"   # Desired output filename

adjust_sub_end_times(input_path, output_path)