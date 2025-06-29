import os
from dotenv import load_dotenv


load_dotenv()

# Load environment variables
LLM_LOCAL_MODEL = os.getenv("LLM_LOCAL_MODEL", "deepseek-r1:14b")
LLM_OPENAI_API_KEY = os.getenv("LLM_OPENAI_API_KEY", "")
LLM_OPENAI_MODEL = os.getenv("LLM_OPENAI_MODEL", "gpt-4o")
LLM_OPENAI_API_BASE = os.getenv("LLM_OPENAI_API_BASE", "")
LLM_USE_OPENAI = os.getenv("LLM_USE_OPENAI", "true").lower() == "true"


HELLO_PROMPT = "Who are you?"
print(LLM_OPENAI_API_KEY)


def test_model_local(model=LLM_LOCAL_MODEL):
    from langchain_ollama import OllamaLLM

    try:
        llm = OllamaLLM(model=model, streaming=True)

        for chunk in llm.stream(HELLO_PROMPT):
            print(chunk, end="", flush=True)
        print()

    except Exception as e:
        print(f"model calling error: {str(e)}")


def test_model_openai():
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=LLM_OPENAI_MODEL,
            streaming=True,
            openai_api_key=LLM_OPENAI_API_KEY,
            openai_api_base=LLM_OPENAI_API_BASE,
        )

        for chunk in llm.stream(HELLO_PROMPT):
            if hasattr(chunk, "content"):
                print(chunk.content, end="", flush=True)
            else:
                print(chunk, end="", flush=True)
        print()

    except Exception as e:
        print(f"model calling error: {str(e)}")


if __name__ == "__main__":
    if LLM_USE_OPENAI:
        print(f"Testing OpenAI model: {LLM_OPENAI_MODEL}")
        test_model_openai()

    else:
        print(f"Testing local model: {LLM_LOCAL_MODEL}")
        test_model_local()
