import pysrt

def merge_short_subs(sentence_subs):
    for i in range(len(sentence_subs) - 1):
        sentence_subs[i].end = sentence_subs[i + 1].start
    print(f"⏭️ Changed SUB end time = next subtitles start time")

    MIN_DURATION_SECONDS = 3.5  # Minimum readable subtitle duration in seconds
    i = 1  # Start from second subtitle
    while i < len(sentence_subs):
        duration = (sentence_subs[i].end.ordinal - sentence_subs[i].start.ordinal) / 1000.0
        if duration < MIN_DURATION_SECONDS:
            # Merge with previous
            prev = sentence_subs[i - 1]
            current = sentence_subs[i]

            prev.text = prev.text.strip() + "... " + current.text.strip()
            prev.end = current.end

            sentence_subs.pop(i)
        else:
            i += 1
    print(f"🤝🤝 Merged sub less than {MIN_DURATION_SECONDS} seconds with previous sub")

subs = pysrt.open('less_than_three.srt')
merge_short_subs(subs)

subs.save('less_than_three_merged.srt')