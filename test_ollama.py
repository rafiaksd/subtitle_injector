import ollama
import time, winsound

def read_text_file(filepath):
    if not filepath.endswith(('.txt', '.srt')):
        raise ValueError("Only .txt and .srt files are supported.")
    
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def write_srt_file(filepath, text):
    if not filepath.endswith('.srt'):
        raise ValueError("File must have a .srt extension.")
    
    with open(filepath, 'w', encoding='utf-8') as file:
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

arabic_sub_text = read_text_file("OUTPUT_TEST_example_sub.srt")

model = 'qwen3:1.7b'  
generation_start_time = time.time()

print(f"🧠🧠 Selected {model}")
print("\n🏁🏁 Generation started\n")
generate_response(model, arabic_sub_text)
get_time_lapsed(generation_start_time)

winsound.Beep(1000,500)
