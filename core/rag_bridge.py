import streamlit as st
import os
import zhipuai
from typing import List

# === 1. 关键修复：所有引用都指向新版路径 ===
# 以前是 langchain.text_splitter，现在是 langchain_text_splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 以前是 langchain.vectorstores，现在是 langchain_community.vectorstores
from langchain_community.vectorstores import Chroma

# 以前是 langchain.docstore.document，现在是 langchain_core.documents
from langchain_core.documents import Document

# 以前是 langchain.embeddings.base，现在是 langchain_core.embeddings
from langchain_core.embeddings import Embeddings


# === 2. 自定义智谱 Embedding 类 (适配 LangChain) ===
class ZhipuEmbedding(Embeddings):
    def __init__(self):
        # 从 secrets 获取 Key
        try:
            api_key = st.secrets["ZHIPU_API_KEY"]
            self.client = zhipuai.ZhipuAI(api_key=api_key)
        except Exception:
            st.error("⚠️ 未找到智谱 API Key，请检查 secrets.toml")
            self.client = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文档"""
        if not self.client: return []
        embeddings = []
        for text in texts:
            try:
                response = self.client.embeddings.create(
                    model="embedding-2",
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([0.0]*1024) # 错误兜底
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """向量化单个问题"""
        if not self.client: return []
        try:
            response = self.client.embeddings.create(
                model="embedding-2",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding query error: {e}")
            return [0.0]*1024

# === 3. 核心功能函数 ===

# 定义持久化存储路径
PERSIST_DIRECTORY = "./chroma_db"

def build_vector_store(text_content):
    """
    将长文本切片并存入 ChromaDB
    """
    if not text_content:
        return "⚠️ 内容为空"
    
    # 1. 切分文本
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 每块500字
        chunk_overlap=50 # 重叠50字，防止语义断裂
    )
    # 将字符串转为 Document 对象
    docs = [Document(page_content=x) for x in text_splitter.split_text(text_content)]
    
    # 2. 存入向量数据库
    try:
        # 使用我们自定义的智谱 Embedding
        embedding_function = ZhipuEmbedding()
        
        # 创建并持久化
        db = Chroma.from_documents(
            documents=docs,
            embedding=embedding_function,
            persist_directory=PERSIST_DIRECTORY
        )
        # 强制保存 (新版 Chroma 自动保存，但为了保险)
        # db.persist() 
        return f"✅ 知识库构建成功！共存入 {len(docs)} 个片段。"
    except Exception as e:
        return f"❌ 构建失败: {str(e)}"

def query_vector_store(question, k=3):
    """
    在数据库中搜索相关内容
    """
    if not os.path.exists(PERSIST_DIRECTORY):
        return "" # 还没建库，返回空
        
    try:
        embedding_function = ZhipuEmbedding()
        db = Chroma(
            persist_directory=PERSIST_DIRECTORY, 
            embedding_function=embedding_function
        )
        
        # 搜索最相似的 k 个片段
        docs = db.similarity_search(question, k=k)
        
        # 合并结果
        context = "\n\n".join([doc.page_content for doc in docs])
        return context
    except Exception as e:
        print(f"搜索失败: {e}")
        return ""