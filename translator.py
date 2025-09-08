import ollama
import time

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

def clear_text_file(filepath):
    if not filepath.endswith('.txt'):
        raise ValueError("Only .txt files are supported.")
    
    # Open in write mode to truncate the file
    open(filepath, 'w', encoding='utf-8').close()

def read_text_file(filepath):
    if not filepath.endswith(('.txt', '.srt')):
        raise ValueError("Only .txt or .srt files are supported.")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def srt_to_lines(srt_text):
    lines = []
    for line in srt_text.splitlines():
        line = line.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        lines.append(line)
    return lines

def translate_line_with_context(model_name, current_line, context_lines):
    # Build prompt with context
    context_prompt = "Previous subtitle lines (context):\n"
    for i, ctx in enumerate(context_lines[-5:], 1):  # Use last 5 lines only
        context_prompt += f"{i}. {ctx}\n"

    prompt = (
        f"{context_prompt}\n"
        f"Now, based on this context, translate ONLY the following line to English:\n"
        f"\"{current_line}\"\n\n"
        f"Use simple English. Only return the translated English sentence. No explanation."
    )

    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        return response['response'].strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return "[TRANSLATION_FAILED]"

ar_file = "translated_lines.txt"

def main(model:str = "gemma3:4b"):
    model_name = model  # make sure this model exists locally via `ollama list`
    print(f" 🧠Using {model_name}")

    filepath = "sharaf_SUB_sentenced.srt"

    print(f"Reading subtitle file: {filepath}")
    arabic_text = read_text_file(filepath)
    arabic_lines = srt_to_lines(arabic_text)

    print(f"Found {len(arabic_lines)} subtitle lines.")
    aligned = []

    for i, current_line in enumerate(arabic_lines):
        context = arabic_lines[max(0, i - 5):i]  # previous 5 lines
        print(f"\nTranslating line {i+1}/{len(arabic_lines)}...")
        english = translate_line_with_context(model_name, current_line, context)
        aligned.append((current_line, english))
        ar_line = f"[AR] {current_line}"
        en_line = f"[EN] {english}"

        output_path = ar_file
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(ar_line + "\n")
            f.write(en_line + "\n\n")

    print(f"\n✅ Saved translated lines to {output_path}")

start_time = time.time()
clear_text_file(ar_file)

main("gemma3:12b")

get_time_lapsed(start_time)
