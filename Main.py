import ollama
response = ollama.chat(
    model="deepseek-r1:7b",
    messages=[
        {"role": "user", "content": "Hello!"},
    ],
)
print(response["message"]["content"])