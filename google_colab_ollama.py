!if [ ! -f /usr/local/bin/ollama ]; then \
    curl -fsSL https://ollama.com/install.sh | sh; \
else \
    echo "Ollama is already installed. Skipping download."; \
fi

import subprocess
import time

subprocess.Popen(["ollama", "serve"])
time.sleep(5)  # Give the server a moment to start up

# 3. Pull the desired model
!ollama pull qwen3:8b

# Now your Python code will work as the server is running
import ollama
def generate_response(model_name: str):
    prompt = f"Who are you? Ans in short"
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        print(response['response'])
        return response['response']
    except Exception as e:
        print(f"Error: {e}")

generate_response("qwen3:8b")