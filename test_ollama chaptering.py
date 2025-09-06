import ollama
import time, winsound, re
from datetime import timedelta

def read_text_file(filepath):
    if not filepath.endswith(('.txt', '.srt')):
        raise ValueError("Only .txt and .srt files are supported.")
    
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def reset_a_file(filepath):    
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write("")

def write_to_file(filepath, text):    
    with open(filepath, 'a', encoding='utf-8') as file:
        file.write(text)

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}   Time elapsed: {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

def get_srt_end_time(srt_text: str) -> str:
    # Regex to find all time ranges
    time_ranges = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', srt_text)

    if not time_ranges:
        raise ValueError("No timestamps found in SRT content.")

    # Get the latest end time (last one in list)
    last_end_time_str = time_ranges[-1][1]

    # Convert to timedelta
    h, m, s_ms = last_end_time_str.split(':')
    s, ms = s_ms.split(',')
    total_seconds = timedelta(
        hours=int(h),
        minutes=int(m),
        seconds=int(s),
        milliseconds=int(ms)
    ).total_seconds()

    # Convert total seconds back to HH:MM:SS
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_response(model_name: str, arabic_subtitle: str):
    sub_end_time = get_srt_end_time(arabic_subtitle)
    print(f"⏱️🏁 DURATION: {sub_end_time}")

    old_prompt = f"""
Analyze the arabic transcript and identify the main topics or "chapters". For each topic, provide a clear, concise title in simple English, avoiding technical jargon or complex terms. Each topic length be between 3 - 8 mins, not more, not less.

Format the output as a single array, where each element is a sub-array containing the topic title, the start time, and the end time in HH:MM:SS format.

Example format:
[['Topic 1', '00:05:21', '00:06:20'], ['Topic 2', '00:06:29', '00:09:50']]

JUST PROVIDE THE ARRAY, AND ABSOLUTELY NOTHING ELSE!

Arabic Transcript to Analyze:
{arabic_subtitle}
"""
    
    prompt = f"""
You are an expert in transcript topic segmentation

I will give you an Arabic lecture transcript in SRT format. 
Your task is to break it into meaningful topics (or "chapters") based on content and flow.

Each topic must:
- Have a clear, specific, and human-readable title in simple English
- Avoid generic or vague titles like "Introduction", "Overview", "Closing", etc.
- Reflect the actual subject or story being discussed, using natural language
- Be between 3 and 8 minutes long (180–480 seconds)
- End no later than {sub_end_time}
- Topics may overlap if they address distinct ideas in the same time window

🛑 Hard rule: DO NOT generate any timestamp beyond {sub_end_time}

📌 Format:
Return a single array of arrays, each one in this format:
["Topic Title", "Start Time", "End Time"]

✅ Example:
[
  ["Why Ibn Mas'ud Told His Daughters to Read Surah Al-Waqi'ah", "00:00:00", "00:03:45"],
  ["The Prophet’s Advice on Facing Poverty", "00:02:30", "00:06:59"]
]

⚠️ JUST RETURN THE ARRAY. DO NOT add any explanations, notes, markdown, or extra formatting.

Arabic Transcript to Analyze:
{arabic_subtitle}

OUTPUT:
"""

    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        
        print("\n--------------------")
        print("--- LLM Response ---\n")
        print(response['response'])
        print("\n--------------------")
        print("--------------------")

        return response['response']

    except Exception as e:
        print(f"Error: {e}")

arabic_texts = ['test_sub_short.srt', "extremely_long_sub_two.srt"]

models = ['llama3.1:8b', 'gemma3:4b', 'gemma3:12b', 'gemma3n:e4b', 'gpt-oss:20b']
#arabic_texts = ["super_short_sub.srt", "short_sub.srt"]
#models = ['qwen3:0.6b', 'gemma3:1b']

very_start_time = time.time()

file_to_write_result = "model_test_results_chaptering.txt"
reset_a_file(file_to_write_result)

# Store timings
results_table = {model: {} for model in models}

for model in models:
     sub_text_counter = 1
     for arabic_sub_text in arabic_texts:
          arabic_sub_actual_text = read_text_file(arabic_sub_text)

          generation_start_time = time.time()

          print(f"📙📘 SUB {sub_text_counter} - {arabic_sub_text}")
          print(f"🧠🧠 Selected {model}")
          print("\n🏁🏁 Generation started\n")

          got_response = generate_response(model, arabic_sub_actual_text)
          time_taken = get_time_lapsed(generation_start_time)

          results_table[model][arabic_sub_text] = time_taken

          write_to_file(file_to_write_result, f"🧠🧠 Selected {model}\n\n" + got_response + "\n\n" + f"SUB {sub_text_counter} - {arabic_sub_text} - 🧠 {model}: ⏱️⏱️ Time: {str(time_taken)} seconds\n\n🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁\n\n")

          print(f"📙📘 SUB {sub_text_counter} - {arabic_sub_text} - 🧠 {model} : ⏱️⏱️ Time: {str(time_taken)} seconds\n\n🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁")
          print('\n\n')

          sub_text_counter += 1
     
          winsound.Beep(1000,500)

write_to_file(file_to_write_result, "\n\n📊📊📊 Summary of Time Taken (in seconds):\n\n")

# Header
header_row = "Model".ljust(20)
for text_name in arabic_texts:
    header_row += text_name.ljust(25)
write_to_file(file_to_write_result, header_row + "\n")
print(header_row)

# Rows
for model in models:
    row = model.ljust(20)
    for text_name in arabic_texts:
        time_taken = results_table[model].get(text_name, "-")
        row += str(round(time_taken, 2)).ljust(25)
    write_to_file(file_to_write_result, row + "\n")
    print(row)

print()

winsound.PlaySound("success.wav", winsound.SND_FILENAME)
get_time_lapsed(very_start_time)