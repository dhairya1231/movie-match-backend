from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from fastapi.staticfiles import StaticFiles

# Load .env file
load_dotenv()

# Create Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MovieRequest(BaseModel):
    genre: str
    language: str
    mood: str


@app.get("/api")
def home():
    return {
        "message": "Welcome to MovieMatch AI Backend!"
    }


@app.post("/recommend")
def recommend(request: MovieRequest):

    prompt = f"""
Recommend exactly 5 movies.

Genre: {request.genre}
Language: {request.language}
Mood: {request.mood}

Return ONLY in this format:

1.
Movie: Movie Name
Reason: One short sentence explaining why it matches.

2.
Movie: Movie Name
Reason: One short sentence explaining why it matches.

3.
Movie: Movie Name
Reason: One short sentence explaining why it matches.

4.
Movie: Movie Name
Reason: One short sentence explaining why it matches.

5.
Movie: Movie Name
Reason: One short sentence explaining why it matches.

Leave one blank line between each movie.

Do not use markdown.
Do not add any introduction.
Do not add any conclusion.
Return only the recommendations.
"""

    # Retry Gemini request up to 5 times
    for attempt in range(5):

        try:

            print(f"\nAttempt {attempt + 1}...")

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            print("Success!\n")

            return {
                "recommendations": response.text
            }

        except Exception as e:

            print("\n========== ERROR ==========")
            print(type(e))
            print(e)
            print("===========================\n")

            error = str(e)

            # Retry if server is temporarily busy
            if "503" in error:

                print("Gemini server busy.")
                print("Retrying in 3 seconds...\n")

                time.sleep(3)
                continue

            # Stop immediately if quota exceeded
            if "429" in error:

                return {
                    "recommendations": "Daily Gemini API quota exceeded. Please try again tomorrow."
                }

            # Any other error
            return {
                "recommendations": "Unexpected error occurred while generating recommendations."
            }

    # If all retries failed
    return {
        "recommendations": "The recommendation service is temporarily busy. Please try again in a minute."
    }


# Mount static files LAST — serves frontend/index.html at "/", plus style.css, script.js, etc.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")