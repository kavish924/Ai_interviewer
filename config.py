import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DEFAULT_MODEL = "llama-3.1-8b-instant"
