import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("Set GOOGLE_API_KEY first!")

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")