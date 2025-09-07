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

def generate_response(model_name: str, arabic_subtitle: str):
    
    prompt = f"""
Translate every single subtitle into English.
NO SUBTITLE SHOULD OVERLAP WITH ANOTHER SUBTITLE EVER!
In the English translation:
- Replace the word “God” with “Allah”.
- Replace any instance of “peace be upon him” (referring to the Prophet) with “ﷺ”.
- Replace May Allah be Pleased with him with رضي الله عنه
- If there is a Quranic verse in the text, then it should be in quotes, and after the end of the quote, the surah name and verse number should be added, eg Yusuf 12

The final result MUST be formatted in standard .srt subtitle format and only have the TRANSLATED ENGLISH PART.

JUST PROVIDE THE TRANSLATED ENGLISH SUBTITLE PART, NOTHING ELSE:

{arabic_subtitle}
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

arabic_texts = ["short_sub.srt", "medium_long_sub.srt", "very_long_sub.srt"]
models = ['gpt-oss:20b']
#arabic_texts = ["super_short_sub.srt", "short_sub.srt"]
#models = ['qwen3:0.6b', 'gemma3:1b']

very_start_time = time.time()

file_to_write_result = "model_test_results.txt"
reset_a_file(file_to_write_result)

# Store timings
results_table = {model: {} for model in models}

for model in models:
     sub_text_counter = 1

     for arabic_sub_text in arabic_texts:
          generation_start_time = time.time()

          print(f"📙📘 SUB {sub_text_counter} - {arabic_sub_text}")
          print(f"🧠🧠 Selected {model}")
          print("\n🏁🏁 Generation started\n")

          got_response = generate_response(model, read_text_file(arabic_sub_text))
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

"""
gemma3:1b	super_short_sub.srt	     17.76 seconds
gemma3:1b	short_sub.srt	          30.07 seconds
gemma3:1b	medium_long_sub.srt	     29.66 seconds
gemma3:1b	very_long_sub.srt	     44.69 seconds
gemma3:4b	super_short_sub.srt	     49.69 seconds
gemma3:4b	short_sub.srt	          114.8 seconds
gemma3:4b	medium_long_sub.srt	     241.93 seconds
"""