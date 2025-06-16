from google import genai 
from google.genai import types 
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

class Gemini_test:
    def __init__(self):
        print("api_key:-",os.getenv("GEMINI_API_KEY"))
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


    async def generate(self,prompt:str):

        try:
            response = await self.client.aio.models.generate_content(
                model = 'gemini-2.0-flash',
                contents = prompt,
                config = types.GenerateContentConfig(
                    temperature=0.3,
                    top_p = 0.8,
                    max_output_tokens=1024,
                ),
            )
            if not (response.candidates 
            and (first := response.candidates[0]).content 
            and (parts := first.content.parts) 
            and (text := parts[0].text)):
                raise ValueError("Invalid response structure from Gemini")
        
            clean_text = ' '.join(text.split())
            return clean_text
            


        except Exception as e:
            raise ValueError(f"Gemini Generation Failed: {str(e)}")




gemini = Gemini_test()

prompt = "Explain the purpose of the cash flow statement."
response = asyncio.run(gemini.generate(prompt))
print(response)