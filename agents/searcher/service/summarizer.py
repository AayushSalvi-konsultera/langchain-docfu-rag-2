# from google import genai 
# from google.genai import types 
# import os
# import asyncio
# from dotenv import load_dotenv
# from typing import Optional

# load_dotenv()

# class GeminiSummarizer:
#     def __init__(self):
#         self.api_key = os.getenv("GEMINI_API_KEY")
#         if not self.api_key:
#             raise ValueError("GEMINI_API_KEY not found in environment variables")
#         self.client = genai.Client(api_key=self.api_key)

#     async def generate(self, prompt: str) -> Optional[str]:
#         """Generate a summary using Gemini API"""
#         try:
#             response = await self.client.aio.models.generate_content(
#                 model='gemini-2.0-flash',
#                 contents=prompt,
#                 config=types.GenerateContentConfig(
#                     temperature=0.3,
#                     top_p=0.8,
#                     max_output_tokens=1024,
#                 ),
#             )
            
#             if not (response.candidates 
#                    and (first := response.candidates[0]).content 
#                    and (parts := first.content.parts) 
#                    and (text := parts[0].text)):
#                 raise ValueError("Invalid response structure from Gemini")
        
#             # Clean and format the text
#             clean_text = ' '.join(text.split())
#             return clean_text

#         except Exception as e:
            
#             return None

# # Global instance (optional, you can also create instances as needed)
# summarizer = GeminiSummarizer()

# summary.py
from google import genai 
from google.genai import types 
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

class GeminiSummarizer:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    async def summarize_content(self, content: str, query: str = None) -> str:
        """Summarize the given link using Gemini"""
        try:
            prompt = f"Please provide a concise summary (100-150 words) of the following content"
            if query:
                prompt += f" focusing on how it relates to '{query}':\n\n{content}"
            else:
                prompt += f":\n\n{content}"
            
            response = await self.client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
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
            raise ValueError(f"Summarization failed: {str(e)}")

# Create a global instance for easy importing
summarizer = GeminiSummarizer()