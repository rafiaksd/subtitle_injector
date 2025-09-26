import ollama

def gen():
     response = ollama.generate(model="gpt-oss:20b", prompt="write 2000 word story")
     response = response['response'].strip()
     print(f"\nRESPONSE: {response}")

     return response

for i in range(1000):
     print(f"Turn {i+1}")
     gen()