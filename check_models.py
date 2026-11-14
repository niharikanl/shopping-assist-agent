from pathlib import Path
from google import genai

api_key = None

for line in Path(".env").read_text().splitlines():
    if line.startswith("GEMINI_API_KEY="):
        api_key = line.split("=", 1)[1].strip().strip('"')
        break

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Reply with exactly: Gemini connection successful."
    )
    print("\nRESULT:")
    print(response.text)

except Exception as error:
    print("\nERROR:")
    print(type(error).__name__)
    print(error)