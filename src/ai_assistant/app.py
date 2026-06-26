import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .governed_copilot import answer_question
from .prompts import SYSTEM_INSTRUCTION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskAgent:
    """
    RiskAgent handles interactions with the configured Google GenAI model.

    The Google SDK is imported lazily so the offline demo and CI can run without
    an external provider installed or configured.
    """

    def __init__(self, model_name: str | None = None):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ValueError("google-genai is not installed. Run `make bootstrap` first.") from exc

        self.model_name = model_name or os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        before_sleep=lambda retry_state: logger.warning(
            f"Rate limit hit or error. Retrying in {retry_state.next_action.sleep} seconds..."
        ),
    )
    def ask(self, prompt: str) -> str:
        """Send a prompt to the configured model and return its response text."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.config,
        )
        return response.text or ""


class OfflineGovernedRiskAgent:
    """Deterministic no-key copilot used for demos, CI and recruiter walkthroughs."""

    def __init__(self, corpus_paths: list[Path] | None = None):
        self.corpus_paths = corpus_paths

    def ask(self, prompt: str) -> str:
        audit_path = os.getenv("AI_AUDIT_PATH")
        answer = answer_question(
            prompt,
            corpus_paths=self.corpus_paths,
            audit_path=Path(audit_path) if audit_path else None,
        )
        return answer.response


def build_risk_agent() -> RiskAgent | OfflineGovernedRiskAgent:
    load_dotenv()
    demo_mode = os.getenv("AI_DEMO_MODE", "0").lower() in {"1", "true", "yes"}
    if demo_mode or not os.getenv("GOOGLE_API_KEY"):
        return OfflineGovernedRiskAgent()
    return RiskAgent()


def main() -> None:
    print("--- FinBank Governed Risk Assistant ---")
    try:
        agent = build_risk_agent()
        print("Assistant ready. Type 'exit' to quit.")

        while True:
            user_input = input("\n[User]: ")
            if user_input.lower() in ["exit", "quit", "sair"]:
                break

            print("\n[Assistant]: ", end="", flush=True)
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
