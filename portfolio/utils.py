import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def ask_llm(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key.strip() == "":
        return "ERROR_MISSING_KEY"

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    except openai.AuthenticationError:
        return "ERROR_INVALID_KEY"
    except Exception as e:
        return f"ERROR_GENERIC: {str(e)}"