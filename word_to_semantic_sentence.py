
import pysrt, time
from wtpsplit import SaT

very_start = time.time()

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")


MAX_DURATION_SECONDS = 12
THRESHOLD = 0.2

def generate_sentence_srt_with_pysrt(input_srt_path, output_srt_path):
    # Step 1: Load word-level SRT
    subs = pysrt.open(input_srt_path, encoding="utf-8")

    # Step 2: Build full text and track word character spans
    full_text = ""
    spans = []  # List of (start_char_index, end_char_index)
    for sub in subs:
        start_idx = len(full_text)
        full_text += sub.text.strip() + " "
        end_idx = len(full_text)
        spans.append((start_idx, end_idx))

    # Step 3: Sentence segmentation
    sat = SaT("sat-12l-sm", language="ar", style_or_domain="general")
    sentences = sat.split(full_text, threshold=THRESHOLD)

    sentence_subs = []
    for sentence in sentences:
        sent_start = full_text.find(sentence)
        sent_end = sent_start + len(sentence)

        # Map to word-level indices
        first_word_idx = None
        last_word_idx = None
        for i, (s, e) in enumerate(spans):
            if s >= sent_start and first_word_idx is None:
                first_word_idx = i
            if e <= sent_end:
                last_word_idx = i

        if first_word_idx is not None and last_word_idx is not None:
            word_indices = list(range(first_word_idx, last_word_idx + 1))
            if not word_indices:
                print(f"⚠️ Skipping empty range for sentence: \"{sentence.strip()}\"")
                continue

            current_chunk = []
            chunk_start_idx = word_indices[0]
            chunk_start_time = subs[chunk_start_idx].start

            for i in word_indices:
                current_chunk.append(i)
                chunk_end_time = subs[i].end
                duration = (chunk_end_time.ordinal - chunk_start_time.ordinal) / 1000.0

                # If the chunk exceeds 8 seconds or this is the last word
                is_last_word = i == word_indices[-1]
                if duration > MAX_DURATION_SECONDS or is_last_word:
                    if duration > MAX_DURATION_SECONDS and len(current_chunk) > 1:
                        # Remove last word and process current_chunk
                        last = current_chunk.pop()
                        i -= 1  # Step back to reprocess last word
                        chunk_end_time = subs[current_chunk[-1]].end
                        is_last_word = False  # still more to go
                    else:
                        last = None  # nothing to reprocess

                    text = ' '.join(subs[j].text.strip() for j in current_chunk)
                    sentence_subs.append(pysrt.SubRipItem(
                        index=len(sentence_subs) + 1,
                        start=chunk_start_time,
                        end=chunk_end_time,
                        text=text
                    ))

                    # Prepare for next chunk
                    if last is not None:
                        current_chunk = [last]
                        chunk_start_time = subs[last].start
                    else:
                        current_chunk = []
                        if not is_last_word:
                            chunk_start_time = subs[i + 1].start

    # Save final SRT
    new_srt = pysrt.SubRipFile(items=sentence_subs)
    new_srt.save(output_srt_path, encoding="utf-8")
    print(f"✅ Saved sentence-level SRT to: {output_srt_path}")

generate_sentence_srt_with_pysrt("high degree of worship to allah.srt", "hok.srt")

get_time_lapsed(very_start)