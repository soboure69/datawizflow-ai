from ollama import Client

client = Client(base_url="http://localhost:11434")

resp = client.chat(
    model="mistral",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Réponds uniquement: OK OLLAMA"},
    ],
)

print(resp["message"]["content"])