import os
from pathlib import Path

from dotenv import load_dotenv

from .governed_copilot import answer_question


class RiskAgent:
    """Online model adapter that always uses the governed copilot pipeline."""

    def __init__(
        self,
        model_name: str | None = None,
        corpus_paths: list[Path] | None = None,
        audit_path: Path | None = None,
    ):
        load_dotenv()
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        try:
            from google import genai  # noqa: F401
        except ImportError as exc:
            raise ValueError("google-genai is not installed. Run `make bootstrap` first.") from exc

        self.model_name = model_name or os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
        self.corpus_paths = corpus_paths
        self.audit_path = audit_path

    def ask(self, prompt: str) -> str:
        answer = answer_question(
            prompt,
            corpus_paths=self.corpus_paths,
            audit_path=self.audit_path,
            model_name=self.model_name,
        )
        return answer.response


class OfflineGovernedRiskAgent:
    """Deterministic no-key copilot used for demos, CI and recruiter walkthroughs."""

    def __init__(
        self,
        corpus_paths: list[Path] | None = None,
        audit_path: Path | None = None,
    ):
        self.corpus_paths = corpus_paths
        self.audit_path = audit_path

    def ask(self, prompt: str) -> str:
        answer = answer_question(
            prompt,
            corpus_paths=self.corpus_paths,
            audit_path=self.audit_path,
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
