import os
import time
import logging
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from prompts import SYSTEM_INSTRUCTION

load_dotenv()

class RiskAgent:
    """
    RiskAgent handles interactions with the Gemma 4 model for financial risk analysis.
    It implements robust retry logic to stay within the 15 RPM free tier limit.
    """
    
    def __init__(self, model_name: str = "gemma-4-31b-it"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_INSTRUCTION
        )
        self.chat = self.model.start_chat(history=[])


    @retry(
        retry=retry_if_exception_type(Exception), # In a real scenario, use specific RateLimit exception
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        before_sleep=lambda retry_state: logger.warning(
            f"Rate limit hit or error. Retrying in {retry_state.next_action.sleep} seconds..."
        )
    )
    def ask(self, prompt: str) -> str:
        """
        Sends a prompt to Gemma 4 and returns the response.
        Includes retry logic for handling the 15 RPM limit.
        """
        response = self.chat.send_message(prompt)
        return response.text

def main():
    print("--- FinBank Risk Assistant (Powered by Gemma 4 31b) ---")
    try:
        agent = RiskAgent()
        print("Assistant ready. Type 'exit' to quit.")
        
        while True:
            user_input = input("\n[User]: ")
            if user_input.lower() in ["exit", "quit", "sair"]:
                break
                
            print("\n[Gemma 4]: ", end="", flush=True)
            try:
                response = agent.ask(user_input)
                print(response)
            except Exception as e:
                print(f"\nError: {e}")
                
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
