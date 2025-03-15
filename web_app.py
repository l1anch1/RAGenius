from flask_cors import CORS  
import os  
import sys  
from flask import Flask, request, jsonify, render_template, Response, stream_with_context  
import json  
import time  

# 确保应用模块可导入  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  

app = Flask(__name__,  
            template_folder='web/templates',  
            static_folder='web/static')  
CORS(app)  # 允许跨域请求  

# 存储全局变量  
global_qa_chain = None  
global_vector_db = None  


@app.route('/')  
def index():  
    """提供主页"""  
    return render_template('index.html')  


@app.route('/api/query/stream', methods=['POST', 'GET'])  
def stream_query_knowledge_base():  
    """流式处理知识库查询"""  
    if not global_qa_chain:  
        return jsonify({"status": "error", "message": "知识库未初始化，请先构建知识库"})  

        # 从POST或GET参数获取查询  
    if request.method == 'POST':  
        data = request.get_json()  
        query = data.get('query', '')  
    else:  # GET  
        query = request.args.get('q', '')  

    if not query.strip():  
        return jsonify({"status": "error", "message": "查询内容不能为空"})  

    def generate():  
        # 修改LLM回调处理以支持流式输出  
        class StreamingCallback:  
            def __init__(self):  
                self.text = ""  

            def on_llm_new_token(self, token, **kwargs):  
                self.text += token  
                # 发送当前片段作为SSE事件  
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"  

        from app.core.model_utils import get_llm  
        from app.core.document_processor import get_vector_store  
        from app.core.retrieval_chain import create_qa_chain  

        # 创建流式回调  
        streaming_callback = StreamingCallback()  

        try:  
            # 获取相关文档  
            vector_db = get_vector_store()  
            docs = vector_db.similarity_search(query, k=3)  

            # 构建上下文  
            context = "\n\n".join([doc.page_content for doc in docs])  

            # 获取带流式回调的LLM  
            streaming_llm = get_llm(streaming=True)  

            # 构建提示  
            from app.core.retrieval_chain import FINANCE_QA_PROMPT_TEMPLATE  
            from langchain_core.prompts import PromptTemplate  

            prompt = PromptTemplate(template=FINANCE_QA_PROMPT_TEMPLATE,  
                                    input_variables=["context", "question"])  

            # 准备源文档信息但暂不发送 - 修改为基于内容去重  
            sources = []  
            unique_contents = set()  # 用于跟踪已添加的文档内容  
            
            for doc in docs[:3]:  
                content = doc.page_content.strip()  
                source_name = doc.metadata.get('source', '未知') if hasattr(doc, 'metadata') else '未知'  
                
                # 如果这个内容还没有添加过，才添加它  
                if content not in unique_contents:  
                    source = {  
                        "content": content,  
                        "source": source_name  
                    }  
                    sources.append(source)  
                    unique_contents.add(content)  

            # 构建完整提示  
            full_prompt = prompt.format(context=context, question=query)  

            # 启动流式生成 - 使用callback流式处理  
            for chunk in streaming_llm.stream(full_prompt):  
                yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"  
                time.sleep(0.01)  # 小延迟使流更自然  

            # 文本生成完成后，发送源文档信息  
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"  

            # 发送完成信号  
            yield f"data: {json.dumps({'type': 'end'})}\n\n"  

        except Exception as e:  
            error_msg = str(e)  
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"  

    return Response(stream_with_context(generate()),  
                    mimetype='text/event-stream',  
                    headers={'Cache-Control': 'no-cache',  
                             'X-Accel-Buffering': 'no'})  


@app.route('/api/rebuild', methods=['POST'])  
def rebuild_knowledge_base():  
    """重建知识库"""  
    global global_qa_chain, global_vector_db  

    try:  
        from app.core.document_processor import build_knowledge_base, get_vector_store  
        from app.core.retrieval_chain import create_qa_chain  
        from app.core.model_utils import llm  

        success = build_knowledge_base()  
        if success:  
            global_vector_db = get_vector_store()  
            global_qa_chain = create_qa_chain(llm, global_vector_db)  
            return jsonify({"status": "success", "message": "知识库重建成功"})  
        else:  
            return jsonify({"status": "error", "message": "知识库重建失败"})  
    except Exception as e:  
        return jsonify({"status": "error", "message": f"重建知识库失败: {str(e)}"})  


@app.route('/api/documents', methods=['GET'])  
def get_documents():  
    """获取文档列表"""  
    try:  
        from app.config import DOCUMENTS_DIR  

        if not os.path.exists(DOCUMENTS_DIR):  
            return jsonify({"status": "success", "documents": []})  

        documents = []  
        for file_name in os.listdir(DOCUMENTS_DIR):  
            file_path = os.path.join(DOCUMENTS_DIR, file_name)  
            if os.path.isfile(file_path):  
                documents.append(file_name)  

        return jsonify({"status": "success", "documents": documents})  
    except Exception as e:  
        return jsonify({"status": "error", "message": f"获取文档列表失败: {str(e)}"})  


@app.route('/api/info', methods=['GET'])  
def get_system_info():  
    """获取系统信息""" 
    try:  
        from app.config import DEFAULT_LLM_MODEL, DEFAULT_EMBEDDING_MODEL, MODEL_NUM_THREAD  

        return jsonify({  
            "status": "success",  
            "model": DEFAULT_LLM_MODEL, 
            "embedding_model": DEFAULT_EMBEDDING_MODEL,  
            "threads": MODEL_NUM_THREAD,  
            "initialized": global_qa_chain is not None  
        })  
    except Exception as e:  
        return jsonify({"status": "error", "message": f"获取系统信息失败: {str(e)}"})  


def init_app():  
    """初始化Web应用"""  
    global global_qa_chain, global_vector_db  

    try:  
        from app.core.document_processor import get_vector_store  
        from app.core.retrieval_chain import create_qa_chain  
        from app.core.model_utils import llm, get_embeddings  

        print("初始化知识库组件...")  
        # 预先加载嵌入模型（只加载一次）  
        embeddings = get_embeddings()  
        if not embeddings:  
            print("无法加载嵌入模型，应用可能无法正常工作")  
            return  
        
         # 使用同一个嵌入模型实例  
        global_vector_db = get_vector_store(embeddings)  
        if global_vector_db:  
            global_qa_chain = create_qa_chain(llm, global_vector_db, embeddings)  
            print("成功加载向量数据库和初始化QA链")  
        else:  
            global_qa_chain = None  
            print("警告: 向量数据库未找到，请先构建知识库")  

    except Exception as e:  
        print(f"初始化应用时出错: {str(e)}")  
        import traceback  
        traceback.print_exc()  


if __name__ == "__main__":  
    import argparse  

    parser = argparse.ArgumentParser(description="启动金融知识库Web应用")  
    parser.add_argument("--port", type=int, default=5000, help="Web服务端口")  
    parser.add_argument("--model", type=str, default="deepseek-r1:14b", help="使用的模型")  
    parser.add_argument("--embedding-model", type=str, default="all-MiniLM-L6-v2", help="嵌入模型")  
    parser.add_argument("--num-threads", type=int, default=4, help="模型线程数")  
    args = parser.parse_args()  

    # 设置环境变量  
    os.environ["DEFAULT_MODEL"] = args.model 
    os.environ["DEFAULT_EMBEDDING_MODEL"] = args.embedding_model  
    os.environ["MODEL_NUM_THREAD"] = str(args.num_threads)  

    # 初始化应用  
    init_app()

    # 启动Web服务  
    print(f"启动Web服务在 http://localhost:{args.port}")  
    app.run(host='0.0.0.0', port=args.port, debug=False)  