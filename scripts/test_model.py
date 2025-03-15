from app.core.model_utils import llm

HELLO_PROMPT = "Who are you?"


def test_deepseek_model():
    try:
        llm.invoke(HELLO_PROMPT)
    except Exception as e:
        print(f"Model calling error: {str(e)}")


if __name__ == "__main__":
    test_deepseek_model()
