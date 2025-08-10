import ollama
import subprocess, time, winsound 

very_time_start = time.time()

def get_time_lapsed(start_time, emojis="⏰⏱️"):
    now_time = time.time()
    time_elapse = now_time - start_time
    print(f"{emojis}  ⏰⏱️⏰ {time_elapse:.2f} seconds\n")
    return round(time_elapse, 2)

def srt_to_short(srt_string):
     output_list = []

     lines = [line.strip() for line in srt_string.strip().split('\n') if line.strip()]

     i = 0
     while i < len(lines):
          i += 1 #skip seqeuence number

          #get timestamps
          timestamp_line = lines[i]
          start_time, end_time = timestamp_line.split('-->')
          i+= 1

          #get all subtitle text until next seq number
          subtitle_text = []
          while i < len(lines) and not lines[i].isdigit():
               subtitle_text.append(lines[i])
               i+= 1

          #join text lines and format the output
          full_text = ''.join(subtitle_text)
          output_list.append(f"{full_text} {start_time} {end_time}")

     text_to_return = ""

     for line in output_list:
          text_to_return += line + "\n"
     return text_to_return

model_ollama = "gpt-oss:20b"
print(f"🧠🧠 Model using: {model_ollama}")

arabic_sub_file = "subs/THINKING GOOD.srt"

with open(arabic_sub_file, 'r', encoding='utf-8') as file:
    arabic_sub_to_use = file.read()
arabic_sub_to_use = srt_to_short(arabic_sub_to_use)

#print(arabic_sub_to_use)

print("🐫🐫 Started fixing sub with ollama...")
def llama_fix_arabic_sub(subtitle_text):
    """Summarizes YouTube captions with balanced clarity, depth, and simplicity."""
    response = ollama.chat(
        model=model_ollama,
        messages=[
            {
                'role': 'user',
                'content': (
                    """You are an expert in Arabic

I will give you Arabic subtitle data that is timestamped at the word level, where each subtitle block contains only a single Arabic word with its own start and end time.

Your task is to group these words into coherent sentence-level subtitles.
You must rely on semantic flow to determine likely sentence boundaries.

Requirements:
- Each output subtitle should contain a complete, meaningful Arabic sentence or clause.
- Sentences should be natural and complete.
- The subtitle's start time should match the first word's start time in the sentence.
- The subtitle's end time should match the first word's starting time in the next sentence.
- Do not remove any words or sentences
- Absolutely MUST keep each subtitle between 6-10 seconds
-- if any sentence do not fit within 6-10 seconds, use ... to show continuation

Example:

Input:
```
كان 00:01:13,920   00:01:14,140
أحمد 00:01:14,140   00:01:14,260
يمشي 00:01:14,260   00:01:14,820
بسرعة 00:01:14,820   00:01:14,940
إلى 00:01:14,940   00:01:15,340
المدرسة 00:01:15,340   00:01:15,680
```

Output:
```
كان أحمد يمشي بسرعة إلى المدرسة 00:01:15,680 00:01:13,920
```

Input:\n"""
                    f"{subtitle_text}\n\nOutput:"
                ),
            },
        ],
    )
    return response['message']['content']

fixed_arabic_sub = llama_fix_arabic_sub(arabic_sub_to_use)
get_time_lapsed(very_time_start); winsound.Beep(1000,500)

local_sub_fixed_text = "local_sub_fixer.txt"
with open(local_sub_fixed_text, "w", encoding="utf-8") as f:
     f.write(fixed_arabic_sub)

subprocess.Popen(['notepad.exe', local_sub_fixed_text])