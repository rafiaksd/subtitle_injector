import ollama
import time, winsound

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

def generate_summary(model_name: str, transcript: str):
    prompt = f"""
     You are a hyper-detailed meeting analyst with a photographic memory and extreme attention to detail.

     You are tasked with generating a **VERY LONG, SUPER DETAILED, COMPREHENSIVE, AND EXHAUSTIVE SUMMARY** of the following meeting transcript.

     ⚠️ **IMPORTANT INSTRUCTIONS — FOLLOW EXACTLY:**

     - Go through the transcript **line by line**, and **extract every single distinct point** that was mentioned — **DO NOT SKIP ANYTHING**, no matter how minor it may seem.
     - **DO NOT MERGE** or compress points. Treat **each unique thought, idea, suggestion, question, answer, action item, or issue raised** as a **separate bullet point**.
     - Include **all important and seemingly unimportant details** — even small clarifications, disagreements, follow-ups, and tangents.
     - If a topic is **revisited later**, capture that **as a new entry** with reference to the earlier discussion if needed.

     🧠 **FORMAT INSTRUCTIONS:**
     - Use **bullet points**, or **numbered sections grouped by topic**, or **speaker-based sections** if that improves clarity.
     - Use **clear, full sentences**.
     - The summary should be **long and highly detailed** — prioritize **completeness over brevity**.
     - Your goal is to give the reader the ability to understand **everything that was discussed**, as if they had been in the meeting themselves.
     - **DO NOT OMIT OR SUMMARIZE** — write out all points explicitly, no matter how repetitive or small.

     🔽 BEGIN TRANSCRIPT 🔽
     {transcript}
     🔼 END TRANSCRIPT 🔼
     """
    
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        
        print("\n--------------------")
        print("--- SUMMARY ---\n\n")
        print(response['response'])
        print("\n\n--------------------")
        print("--------------------")

        return response['response']

    except Exception as e:
        print(f"Error: {e}")

meeting_texts = ["ai_meeting_sub.txt"]
models = ['gemma3:4b', 'qwen3:4b', 'llama3.1:8b', 'qwen3:8b', 'gemma3n:e4b', 'gemma3:12b', 'qwen3:14b']

#arabic_texts = ["super_short_sub.srt", "short_sub.srt"]
#models = ['qwen3:0.6b', 'gemma3:1b']

very_start_time = time.time()

file_to_write_result = "meeting_summary_test_results.txt"
reset_a_file(file_to_write_result)

# Store timings
results_table = {model: {} for model in models}

for model in models:
     sub_text_counter = 1

     for meeting_text in meeting_texts:
          generation_start_time = time.time()

          print(f"📙📘 SUB {sub_text_counter} - {meeting_text}")
          print(f"🧠🧠 Selected {model}")
          print("\n🏁🏁 Generation started\n")

          got_response = generate_summary(model, read_text_file(meeting_text))
          time_taken = get_time_lapsed(generation_start_time)

          results_table[model][meeting_text] = time_taken

          write_to_file(file_to_write_result, f"🧠🧠 Selected {model}\n\n" + got_response + "\n\n" + f"SUB {sub_text_counter} - {meeting_text} - 🧠 {model}: ⏱️⏱️ Time: {str(time_taken)} seconds\n\n🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁\n\n")

          print(f"📙📘 SUB {sub_text_counter} - {meeting_text} - 🧠 {model} : ⏱️⏱️ Time: {str(time_taken)} seconds\n\n🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁")
          print('\n\n')

          sub_text_counter += 1
     
     winsound.Beep(1000,500)

write_to_file(file_to_write_result, "\n\n📊📊📊 Summary of Time Taken (in seconds):\n\n")

# Header
header_row = "Model".ljust(20)
for text_name in meeting_texts:
    header_row += text_name.ljust(25)
write_to_file(file_to_write_result, header_row + "\n")
print(header_row)

# Rows
for model in models:
    row = model.ljust(20)
    for text_name in meeting_texts:
        time_taken = results_table[model].get(text_name, "-")
        row += str(round(time_taken, 2)).ljust(25)
    write_to_file(file_to_write_result, row + "\n")
    print(row)

print()

winsound.PlaySound("success.wav", winsound.SND_FILENAME)
get_time_lapsed(very_start_time)