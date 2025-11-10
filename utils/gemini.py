import os
from google import genai

from config import settings

client = genai.Client(api_key=settings.GENAI_API_KEY)

