import os
from typing import List, Optional
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.core.model_utils import get_embeddings
from app.config import DOCUMENTS_DIR, VECTOR_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP
import app.core.shared_instances as shared


def load_documents(directory_path: str = DOCUMENTS_DIR) -> List[Document]:
    documents = []
    directory = Path(directory_path)

    if not directory.exists() or not directory.is_dir():
        return documents

    for file_path in directory.iterdir():
        if not file_path.is_file() or file_path.name == ".gitkeep":
            continue

        try:
            if file_path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file_path))
                documents.extend(loader.load())
            elif file_path.suffix.lower() == ".csv":
                loader = CSVLoader(str(file_path))
                documents.extend(loader.load())
            elif file_path.suffix.lower() == ".txt":
                loader = TextLoader(str(file_path), encoding="utf-8")
                documents.extend(loader.load())

        except Exception as e:
            print("Unexpected error:", e)
            pass

    return documents


def process_documents(documents: List[Document]) -> List[Document]:
    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "!", "?", "！", "？", ".", " ", ""],
        length_function=len,
    )

    chunks = text_splitter.split_documents(documents)
    return chunks


def create_vector_store(
    chunks: List[Document], embedding_model=None
) -> Optional[Chroma]:
    if not chunks:
        return None
    try:

        embeddings = get_embeddings()
        if embeddings is None:
            return False

        if os.path.exists(VECTOR_DB_PATH):
            print(f"检测到现有向量库: {VECTOR_DB_PATH}")

            # 尝试清理现有的Chroma数据库
            try:
                # 释放可能存在的连接
                import sqlite3
                import gc

                gc.collect()

                # 尝试关闭所有可能的sqlite连接
                sqlite_path = os.path.join(VECTOR_DB_PATH, "chroma.sqlite3")
                if os.path.exists(sqlite_path):
                    try:
                        # 尝试创建一个临时连接并立即关闭，可能帮助释放锁
                        conn = sqlite3.connect(sqlite_path)
                        conn.close()
                    except Exception as e:
                        print(f"尝试操作数据库时出错: {str(e)}")

                import time

                time.sleep(1)

                # 不删除整个目录，而是尝试创建/覆盖Collections
                print("将使用现有目录但刷新数据")
            except Exception as e:
                print(f"清理过程中出错: {str(e)}")
        else:
            os.makedirs(VECTOR_DB_PATH, exist_ok=True)

        # 创建或刷新向量库
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=VECTOR_DB_PATH,
        )

        print("向量库创建成功")
        return vector_db
    except Exception as e:
        print(f"创建向量库时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def get_vector_store(force_reload: bool = False) -> Optional[Chroma]:
    if shared.vector_db is not None and not force_reload:
        return shared.vector_db
    try:
        embedding_model = get_embeddings()
        if embedding_model is None:
            print("无法获取嵌入模型，向量数据库加载失败")
            return None

        if os.path.exists(VECTOR_DB_PATH):
            shared.vector_db = Chroma(
                persist_directory=VECTOR_DB_PATH, embedding_function=embedding_model
            )
            return shared.vector_db
        else:
            return None
    except Exception as e:
        print(f"Vectordb loading error: {str(e)}")
        return None


def build_knowledge_base(documents_dir: str = DOCUMENTS_DIR) -> bool:
    try:
        documents = load_documents(documents_dir)
        if not documents:
            return False
        chunks = process_documents(documents)

        if not chunks:
            return False
        embedding_model = get_embeddings()

        if not embedding_model:
            return False

        vector_db = create_vector_store(chunks, embedding_model)
        vector_db_exists = vector_db is not None
        print(vector_db_exists)
        return vector_db_exists
    except Exception as e:
        print("Vectordb building error:", e)
        return False
