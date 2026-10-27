from google import genai
import os
from dotenv import load_dotenv
load_dotenv()


client = genai.Client()


interaction = client.interactions.create(
    model="gemini-3.8-flash",
    system_instruction="you are a professional resume writer with 30 year of experiance"
                       "in helping create perfect resumes for diffrent job postings",
    input="create a markdown resumes for the average software dev"
)

print(interaction.output_text)