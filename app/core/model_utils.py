from typing import Optional
from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.embeddings import Embeddings

from app.config import (
    DEFAULT_LLM_MODEL, DEFAULT_EMBEDDING_MODEL, MODEL_TEMPERATURE, MODEL_TOP_P,
    MODEL_NUM_CTX, MODEL_NUM_PREDICT, MODEL_NUM_THREAD
)
import app.core.shared_instances as shared  

def get_llm(
        model: str = DEFAULT_LLM_MODEL,
        temperature: float = MODEL_TEMPERATURE,
        top_p: float = MODEL_TOP_P,
        num_ctx: int = MODEL_NUM_CTX,
        num_predict: int = MODEL_NUM_PREDICT,
        streaming: bool = True,
        **kwargs
) -> Optional[OllamaLLM]:
    """
    初始化并返回Ollama模型实例

    Args:
        model: Ollama中的模型名称，默认为deepseek-r1:14b
        temperature: 生成的随机性 (0.0-1.0)
        top_p: 用于核采样的概率质量 (0.0-1.0)
        num_ctx: 上下文窗口大小
        num_predict: 单次调用生成的最大令牌数
        streaming: 是否启用流式输出
        **kwargs: 传递给Ollama的其他参数

    Returns:
        配置好的LLM实例或None (如果初始化失败)
    """
    # 配置回调
    callbacks = []
    if streaming and StreamingStdOutCallbackHandler is not None:
        callbacks.append(StreamingStdOutCallbackHandler())

    try:
        model_kwargs = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "num_ctx": num_ctx,
            "num_predict": num_predict,
            "num_thread": MODEL_NUM_THREAD,
            "callbacks": callbacks,
            **kwargs
        }

        shared.llm_model = OllamaLLM(**model_kwargs)
        print(f"成功初始化Ollama模型: {model}")
        return shared.llm_model

    except Exception as e:
        print(f"初始化模型时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


def get_device():  
    import torch  
    if torch.cuda.is_available():  
        return 'cuda'  
    return 'cpu'  


def get_embeddings(
        model_name: str = DEFAULT_EMBEDDING_MODEL, 
        force_reload=False
) -> Optional[Embeddings]:  

    if shared.embedding_model is not None and not force_reload:  
        return shared.embedding_model  
    
    try:  
        import os  
        from langchain_huggingface import HuggingFaceEmbeddings  
        
        # 设置固定的模型缓存目录  
        current_dir = os.path.dirname(os.path.abspath(__file__))  
        app_root = os.path.dirname(current_dir)  
        cache_dir = os.path.join(app_root, "models_cache")  
        os.makedirs(cache_dir, exist_ok=True)  
        
        # 设置环境变量确保使用指定缓存目录  
        os.environ["HF_HOME"] = cache_dir  # 只使用新的环境变量名  

        device = get_device()  
        model_kwargs = {'device': device}  
        encode_kwargs = {'normalize_embeddings': True}  
        
        shared.embedding_model = HuggingFaceEmbeddings(  
            model_name=model_name,  
            model_kwargs=model_kwargs,  
            encode_kwargs=encode_kwargs,  
            cache_folder=cache_dir  
        )  
        
        return shared.embedding_model   
    except Exception as e:  
        print(f"fail to load embedding model: {str(e)}")  
        import traceback  
        traceback.print_exc()  
        return None  


llm = get_llm()
if llm is None:
    print("默认LLM模型初始化失败")
else:
    print("默认LLM模型初始化成功")
