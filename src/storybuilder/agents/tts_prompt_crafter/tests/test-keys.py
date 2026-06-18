import os

from google import genai

try:
    print("Testing Vertex AI Client...")
    client = genai.Client(vertexai=True, project="storage-499607", location="us-central1")
    print("Client initialized successfully.")
    print("Attempting to generate content...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello!",
    )
    print(f"Vertex AI SUCCESS! Response: {response.text}")
except Exception as e:
    print(f"Vertex AI FAILED: {e}")
