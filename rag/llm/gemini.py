#import google.generativeai as genai
# import os
# from tenacity import retry, stop_after_attempt, wait_exponential

# class GeminiClient:
#     def __init__(self):
#         # Configure with API key from environment
#         genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#         self.model = genai.GenerativeModel('gemini-1.5-flash')  # Or your preferred model
        
#         self.generation_config = {
#             "temperature": 0.3,
#             "top_p": 0.8,
#             "max_output_tokens": 1024,
#             "timeout": 30  # Seconds
#         }

#     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
#     async def generate(self, prompt: str) -> str:
#         """Generate response using Gemini API"""
#         try:
#             response = await self.model.generate_content_async(
#                 contents=prompt,
#                 generation_config=self.generation_config
#             )
#             return response.text
#         except Exception as e:
#             raise ValueError(f"Gemini generation failed: {str(e)}")


# import google.generativeai as genai
# import os
# from tenacity import retry, stop_after_attempt, wait_exponential


from google import genai
from google.genai import types
import os
from tenacity import retry, stop_after_attempt, wait_exponential
import json

class GeminiClient:
    def __init__(self):
        # ✅ Required in v0.8.5
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        
        

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(self, prompt: str):
        """Generate response using Gemini API"""
        try:
            # self.generation_config = self.client.models.generate_content(
            # model='gemini-1.5-flash',
            # contents=prompt,
            # config = types.GenerateContentConfig(
            # temperature=0.3,
            # top_p=0.8,
            # max_output_tokens=1024,
            # ),
        #)
            response = await self.client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config = types.GenerateContentConfig(
            temperature=0.5,
            top_p=0.8,
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
            raise ValueError(f"Gemini generation failed: {str(e)}")