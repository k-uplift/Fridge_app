import ollama

res = ollama.chat(model="llama3", messages=[
    {"role": "user", "content": "Hello! Tell me a short joke."}
])

print(res["message"]["content"])
