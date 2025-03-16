from langchain_ollama import OllamaLLM  
from app.config import DEFAULT_LLM_MODEL


HELLO_PROMPT = "Who are you?"  


def test_model(model=DEFAULT_LLM_MODEL):  
    try:  
        llm = OllamaLLM(model=model, streaming=True)  
        
        for chunk in llm.stream(HELLO_PROMPT):  
            print(chunk, end="", flush=True)  
        print()  
        
    except Exception as e:  
        print(f"model calling error: {str(e)}")  


if __name__ == "__main__":  
    test_model()  