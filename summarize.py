import os, re, time, shutil, subprocess, winsound
from pytubefix import YouTube
from pydub import AudioSegment

from tqdm import tqdm

import nemo.collections.asr as nemo_asr
from omegaconf import open_dict

import pysrt
from wtpsplit import SaT
import pyperclip

import yt_dlp

def sanitize_folder_name(name: str, replacement: str = "_") -> str:
    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized = re.sub(illegal_chars, replacement, name)
    sanitized = sanitized.rstrip(". ")
    sanitized = sanitized.lstrip()
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if sanitized.upper() in reserved_names:
        sanitized = f"{sanitized}_safe"
    return sanitized

def format_srt_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    return time.strftime('%H:%M:%S', time.gmtime(int(seconds))) + f",{ms:03d}"

def split_audio(input_audio_path, chunk_length_ms=15 * 1000):
    audio = AudioSegment.from_file(input_audio_path)
    chunks = []
    total_chunks = len(audio) // chunk_length_ms + (1 if len(audio) % chunk_length_ms else 0)
    os.makedirs("chunks_folder", exist_ok=True)
    for i in tqdm(range(0, len(audio), chunk_length_ms), desc="Splitting audio", total=total_chunks):
        chunk = audio[i:i + chunk_length_ms]
        chunk = chunk.set_channels(1)
        chunk_path = f"chunks_folder/chunk_{i // chunk_length_ms}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append((chunk_path, i / 1000.0))
    return chunks

def load_asr_model():
    model = nemo_asr.models.ASRModel.from_pretrained("nvidia/stt_ar_fastconformer_hybrid_large_pcd_v1.0")
    decoding_cfg = model.cfg.decoding
    with open_dict(decoding_cfg):
        decoding_cfg.preserve_alignments = True
        decoding_cfg.compute_timestamps = True
        decoding_cfg.segment_separators = ["?", "!", "."]
        decoding_cfg.word_separator = " "
    model.change_decoding_strategy(decoding_cfg)
    return model

def transcribe_chunks(model, chunks, output_srt_path):
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        subtitle_index = 1
        for chunk_path, chunk_start_sec in tqdm(chunks, desc="Transcribing chunks"):
            hypotheses = model.transcribe([chunk_path], return_hypotheses=True)
            word_timestamps = hypotheses[0].timestamp['word']
            time_stride = 8 * model.cfg.preprocessor.window_stride
            for stamp in word_timestamps:
                start_sec = stamp['start_offset'] * time_stride + chunk_start_sec
                end_sec = stamp['end_offset'] * time_stride + chunk_start_sec
                word = stamp.get('word', stamp.get('char'))
                srt_file.write(f"{subtitle_index}\n")
                srt_file.write(f"{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}\n")
                srt_file.write(f"{word}\n\n")
                subtitle_index += 1
            os.remove(chunk_path)

def generate_semantic_srt(input_srt_path, output_srt_path, threshold=0.25, max_duration=16.0):
    subs = pysrt.open(input_srt_path, encoding="utf-8")
    full_text = ""
    spans = []
    for sub in subs:
        start_idx = len(full_text)
        full_text += sub.text.strip() + " "
        end_idx = len(full_text)
        spans.append((start_idx, end_idx))

    sat = SaT("sat-12l-sm", language="ar", style_or_domain="general")
    sentences = sat.split(full_text, threshold=threshold)

    sentence_subs = []
    for sentence in sentences:
        sent_start = full_text.find(sentence)
        sent_end = sent_start + len(sentence)

        first_word_idx = None
        last_word_idx = None
        for i, (s, e) in enumerate(spans):
            if s <= sent_start < e:
                first_word_idx = i
            if s < sent_end <= e:
                last_word_idx = i

        if first_word_idx is None or last_word_idx is None:
            continue

        word_indices = list(range(first_word_idx, last_word_idx + 1))
        current_chunk = []
        chunk_start_idx = word_indices[0]
        chunk_start_time = subs[chunk_start_idx].start

        i = 0
        while i < len(word_indices):
            idx = word_indices[i]
            current_chunk.append(idx)
            chunk_end_time = subs[idx].end
            duration = (chunk_end_time.ordinal - chunk_start_time.ordinal) / 1000.0
            is_last_word = (i == len(word_indices) - 1)

            if duration > max_duration or is_last_word:
                if duration > max_duration and len(current_chunk) > 1:
                    last = current_chunk.pop()
                    i -= 1
                    chunk_end_time = subs[current_chunk[-1]].end
                else:
                    last = None

                text = ' '.join(subs[j].text.strip() for j in current_chunk)
                sentence_subs.append(pysrt.SubRipItem(
                    index=len(sentence_subs) + 1,
                    start=chunk_start_time,
                    end=chunk_end_time,
                    text=text
                ))

                if last is not None:
                    current_chunk = [last]
                    chunk_start_time = subs[last].start
                else:
                    current_chunk = []
                    if not is_last_word:
                        chunk_start_time = subs[word_indices[i + 1]].start
            i += 1

    for i in range(len(sentence_subs) - 1):
        sentence_subs[i].end = sentence_subs[i + 1].start

    MIN_DURATION_SECONDS = 3
    i = 1
    while i < len(sentence_subs):
        duration = (sentence_subs[i].end.ordinal - sentence_subs[i].start.ordinal) / 1000.0
        if duration < MIN_DURATION_SECONDS:
            prev = sentence_subs[i - 1]
            current = sentence_subs[i]
            prev.text = prev.text.strip() + "... " + current.text.strip()
            prev.end = current.end
            sentence_subs.pop(i)
        else:
            i += 1

    new_srt = pysrt.SubRipFile(items=sentence_subs)
    new_srt.save(output_srt_path, encoding="utf-8")

def process_youtube_video_to_transcript(link, output_video_name, delete_video=True):
    output_video_name = sanitize_folder_name(output_video_name)
    output_dir = os.path.abspath("summaries_direct/" + output_video_name)

    print(f"Making directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # Download YouTube video with pytubefix
    print("Downloading video...")
    try:
        yt = YouTube(link)
        title = sanitize_folder_name(yt.title)
        streams = yt.streams.filter(file_extension='mp4', type='video').order_by('resolution').desc()
        available_streams = [s for s in streams if s.resolution]
        if not available_streams:
            print("No valid video streams found.")
            return
        selected_stream = available_streams[max(0, len(available_streams) - 2)]

        video_path = os.path.join(output_dir, f"{title}_video.mp4")
        audio_path = os.path.join(output_dir, f"{title}_audio.m4a")
        final_video_path = os.path.join(output_dir, f"{title}.mp4")

        print(f"VIDEO downloading beginning for {output_video_name}...")
        selected_stream.download(output_path=output_dir, filename=os.path.basename(video_path))

        if not selected_stream.is_progressive:
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

            print(f"AUDIO downloading beginning for {output_video_name}...")
            audio_stream.download(output_path=output_dir, filename=os.path.basename(audio_path))

            print(f"MERGING AUDIO & VIDEO for {output_video_name}...")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                final_video_path
            ], check=True, capture_output=True)

            os.remove(video_path)
            os.remove(audio_path)
        else:
            os.rename(video_path, final_video_path)

        print(f"Downloaded and merged video saved at: {final_video_path}")

    except Exception as e:
        print(f"Error downloading video: {e}")
        return

    # Split audio for ASR
    print("Splitting audio for transcription...")
    chunks = split_audio(final_video_path)

    # Load ASR model
    print("Loading ASR model...")
    asr_model = load_asr_model()

    # Transcribe chunks
    base_filename = os.path.splitext(os.path.basename(final_video_path))[0]
    word_srt_path = os.path.join(output_dir, f"{base_filename}_word.srt")
    print("Transcribing audio chunks...")
    transcribe_chunks(asr_model, chunks, word_srt_path)

    # Generate semantic sentence-level subtitles
    semantic_srt_path = os.path.join(output_dir, f"{base_filename}_semantic.srt")
    print("Generating semantic subtitles...")
    generate_semantic_srt(word_srt_path, semantic_srt_path)

    os.remove(word_srt_path)
    print(f"💀 Deleted WORD Level subs")
    if delete_video:
        os.remove(final_video_path)
        print(f"💀 Deleted the VIDEO")

    print(f"Transcription complete! Files saved in {output_dir}")
    print(f"Semantic subtitles: {semantic_srt_path}")

    # Optionally copy semantic subtitles content + prompt to clipboard
    prompt_text = "summarize all distinct points in simple english, let no distinct point be left\n\n"
    try:
        with open(semantic_srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        combined_text = prompt_text + srt_content
        pyperclip.copy(combined_text)
        print("Combined semantic subtitles and prompt copied to clipboard!")
    except Exception as e:
        print(f"Could not copy to clipboard: {e}")

    winsound.Beep(1000,500)
    return output_dir

vid_links = [
    "https://youtu.be/o5TLONN2WfE?si=VKuXR9Ag_rkvrWUo",
    "https://youtu.be/tZPycl2SeA0?si=7G9fTgZaVaS4JRDQ",
    "https://youtu.be/obO3OIr26Pc?si=pkSiY8uYtzf9G8Td",
    "https://youtu.be/YUbGp77cT3U?si=kwd9L-XXTxHUOV0B",
    "https://youtu.be/wvOfMAUuhjM?si=12giNR_1cuvoD-8b",
    "https://youtu.be/-vgvSCuoDxU?si=ViNI9_0XbqsttvxU",
    "https://youtu.be/0FhG_M29PVA?si=-LPAPQDKTb8cDRDY",
    "https://youtu.be/PLx_AqRFdO0?si=Q4EnkQTwYyixc3sd",
    "https://youtu.be/4VwP9-RJdoc?si=2E6Mkg7aTjGkHQ6o"
]

vid_links_11_to_15 = [
    "https://youtu.be/9hq64GHCPEw?si=YlXCULjqMpb01YqX",
    "https://youtu.be/crFoCsj0z4k?si=JpSL6Yz4PF5HVqq7",
    "https://youtu.be/XBZ9m2NFaik?si=DaXYXXAp86t_x7Ef",
    "https://youtu.be/HCgxP2MF0jc?si=Jdh4ghic9zef4fPU",
    "https://youtu.be/06b9NZoA2cc?si=liWm6c6F2XC6t8m2",
]
vid_links_16_to_20 = [
    "https://youtu.be/p0Rf5oCrsJM?si=-bvpcWvOWazfIGjY",
    "https://youtu.be/UgeICHbscjA?si=9En9UP7DiPx2r9aW",
    "https://youtu.be/zYePAe7jeLY?si=aZSXcX0Z-XA6HSID",
    "https://youtu.be/GTVJeC9-lTM?si=QbmmbyMtklygqbz9",
    "https://youtu.be/x8RRXXd3C4k?si=S4CSChRTND94RPu6"
]

vid_links_21_to_30 = [
    "https://youtu.be/h4i7daViN1Y?si=1h7WfPusuqxQEG4I",
    "https://youtu.be/wBpL5BXlBCA?si=MBCGFCrgHfSMrj0B",
    "https://youtu.be/aYBIeVavzXI?si=c-yFyrKGcp2trAhA",
    "https://youtu.be/UApZEkruHNY?si=btab8LiyiE1tL2EA",
    "https://youtu.be/pvKxflzP9PQ?si=nte7ZEyxWfjU1ELX",
    "https://youtu.be/wbKD4Qkh2v8?si=mB48IQBydCS_bMom",
    "https://youtu.be/RAab7_KmNPM?si=4ZN8BaTCEWgXfP_H",
    "https://youtu.be/dxSe6Xsl6No?si=cZgNlwd3w2ybE0BA",
    "https://youtu.be/F8xUZhiywFk?si=vxgmOsevUo7WP5ek",
    "https://youtu.be/-tdxsgHcAGA?si=gwJLr9BtjeETxo6t",
]

vid_links_31_to_40 = [
    "https://youtu.be/oCiP40z93Do?si=YFlSoBFaE8wOyLmf",
    "https://youtu.be/v_yWBPx_7us?si=KlzlyelKTe3CweMP",
    "https://youtu.be/WYJB6ydMKzs?si=qnn4D3oaF4GGEw8A",
    "https://youtu.be/TC69YCqtZDY?si=JjQZWbb8DTm_iSly",
    "https://youtu.be/dh_Xem5sLwM?si=4R8bhCcvwiem9eHV",
    "https://youtu.be/7YoLiUJbaJ0?si=-llgjzoCX0WPq529",
    "https://youtu.be/-TMfCZsXcxQ?si=4DD2LRN389taKLCD",
    "https://youtu.be/1H7EOXLZj2w?si=FMI5YGzbb576YHyM",
    "https://youtu.be/kb7eelDGMW0?si=pKuiN9gMBp5rBRBR",
    "https://youtu.be/cwhhNxjqxjo?si=092dGGcvuAsETsSy",
]

vid_links_41_to_48 = [
    "https://youtu.be/TdYw826rv-s?si=n094R_tByhthx7r-",
    "https://youtu.be/sIK2QOiVE3o?si=uGFfeS6p4Y4drCoE",
    "https://youtu.be/oT4E9PMwEwA?si=yEn8fKbw2jaZ81rz",
    "https://youtu.be/UxPYFSphuKw?si=jCv7jOmunRwKX37q",
    "https://youtu.be/ZGpExhqjYi4?si=3O4jRuzczGHO3WE-",
    "https://youtu.be/mhVQYBnXIKg?si=rQpChBOTIbihvNb8",
    "https://youtu.be/F9ilKlEyrrE?si=pf8kghbnlmbzroaD",
    "https://youtu.be/M3k5i0EjiPQ?si=DY-E9on49CGwl5h8",
]

kitab_fitan = [
    "https://youtu.be/zvsUWasouRM?si=DcjvP1o4Y5IUVm-3",
    "https://youtu.be/mGNzp9O5c7w?si=PGOF6EhOj7aLyf7A",
    "https://youtu.be/bo04RFrIB5E?si=YHgu0WdGyhkJPvhB",
    "https://youtu.be/_ww6KheNl5g?si=CLRQD22tTwcVh_A4",
    "https://youtu.be/N7MObu5jt2Y?si=vYNkLdXrzGIHVTpm",
    "https://youtu.be/UJ4mRNAJ1eA?si=iKvxeOzN3Nglvh0W",
    "https://youtu.be/fjQ76vsS90M?si=a2sp_5xyDETs5qzs",
    "https://youtu.be/1rdsg6HIX-g?si=IM-SMQDaDsSG5DMX",
]

sharh_kitab_murtadin_ibn_uthaymin = [
    "https://youtu.be/mGo9iOxL9p0?si=bTDGm-xDeMflaOrp",
    "https://youtu.be/59OkBCOR-t4?si=k0yYFqsqq222090g",
    "https://youtu.be/_lt2_HlVOEw?si=bLeScl6ozT5rSehJ",
    "https://youtu.be/W1J0yrodZbA?si=uoZ7FM7I71TutEiX",
    "https://youtu.be/G-eytRekvEk?si=qmUMhOBwQGnYtG-t",
    "https://youtu.be/c-imSHDuYTA?si=Lpjp0MUg59XcBUXJ",
    "https://youtu.be/b2iWRKHiVM4?si=8ewxJ_S7XrOnOTzV",
    "https://youtu.be/1gT_dAQCoTg?si=9HaCbRI_cqT2eQ-X",
    "https://youtu.be/gcP-skhMw6I?si=WOjt4QtCAL0rqphX",
    "https://youtu.be/qiXQmlE0SLE?si=VWVWp9nffBpxtjKr",
]


def save_videos_with_range(vid_links, base_name, start_num, end_num):
    # Ensure the range is valid
    if start_num < 1 or (end_num-start_num) > len(vid_links):
        print("Start or end number out of range.")
        return

    for i in range(0, (end_num-start_num+1)):
        suffix = str(start_num + i)
        numbered_name = f"{base_name} {suffix}"
        print(f"\n📥 Processing video {i+1}: {numbered_name}")
        output_folder = process_youtube_video_to_transcript(vid_links[i], numbered_name)

def get_video_links_from_playlist(playlist_url):
    # Create a YT-DLP object
    ydl_opts = {
        'quiet': True,  # Suppress unnecessary output
        'extract_flat': True,  # Don't download the videos, just get their info
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract playlist info
        result = ydl.extract_info(playlist_url, download=False)

        # Check if it's a playlist
        if 'entries' in result:
            video_urls = [entry['url'] for entry in result['entries']]
            return video_urls
        else:
            return None

def download_playlists(base_name, playlist_link):
    playlist_vids = (get_video_links_from_playlist(playlist_link))
    print(f"Playlist list got!")
    save_videos_with_range(playlist_vids, base_name, 1, len(playlist_vids))

base_name = "sarim al maslool anqari"
playlist_link = "https://www.youtube.com/playlist?list=PLu0QvMsJToc122Tf51KEvtpborrlhvMIu"

download_playlists(base_name, playlist_link)
#process_youtube_video_to_transcript("https://youtu.be/8nqELTSxEII", "sharh_kitab sarim al maslool abu hafdh")
winsound.PlaySound("victory.wav", winsound.SND_FILENAME)
