"""
RAG Bridge - 基于 ZhipuAI 的检索增强生成功能
使用 ChromaDB 作为向量数据库，ZhipuAI Embedding API 进行文本嵌入
"""

import streamlit as st
from typing import List, Optional
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from chromadb.config import Settings

# 兼容不同版本的 LangChain
try:
    from langchain.embeddings.base import Embeddings
except ImportError:
    try:
        from langchain_core.embeddings import Embeddings
    except ImportError:
        from langchain.schema.embeddings import Embeddings

try:
    import zhipuai
except ImportError:
    raise ImportError("请安装 zhipuai 库: pip install zhipuai")


class ZhipuEmbedding(Embeddings):
    """自定义 ZhipuAI Embedding 类，实现 LangChain Embeddings 接口"""
    
    def __init__(self, api_key: str):
        """
        初始化 ZhipuAI Embedding
        
        Args:
            api_key: ZhipuAI API Key
        """
        if not api_key:
            raise ValueError("ZhipuAI API Key 不能为空")
        self.client = zhipuai.ZhipuAI(api_key=api_key)
        self.model = "embedding-2"  # ZhipuAI 的嵌入模型
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                # ZhipuAI API 返回格式: response.data[0].embedding
                embedding = response.data[0].embedding
                embeddings.append(embedding)
            except Exception as e:
                st.error(f"❌ 嵌入文档时出错: {e}")
                # 返回零向量作为降级处理
                embeddings.append([0.0] * 1024)  # embedding-2 返回 1024 维向量
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            st.error(f"❌ 嵌入查询时出错: {e}")
            # 返回零向量作为降级处理
            return [0.0] * 1024


def _get_embedding_instance() -> ZhipuEmbedding:
    """
    获取 ZhipuAI Embedding 实例（带缓存）
    
    Returns:
        ZhipuEmbedding 实例
    """
    try:
        api_key = st.secrets["ZHIPU_API_KEY"]
    except KeyError:
        st.error("⚠️ 未找到 ZHIPU_API_KEY，请在 Streamlit secrets 中配置")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ 读取 API Key 时出错: {e}")
        st.stop()
    
    return ZhipuEmbedding(api_key=api_key)


@st.cache_resource
def _get_vector_store(_embedding: ZhipuEmbedding, collection_name: str = "knowledge_base"):
    """
    获取或创建 ChromaDB 向量存储（带缓存）
    
    Args:
        _embedding: Embedding 实例（带下划线前缀表示仅用于缓存键）
        collection_name: 集合名称
        
    Returns:
        Chroma 向量存储实例
    """
    persist_directory = "./chroma_db"
    
    # 确保目录存在
    os.makedirs(persist_directory, exist_ok=True)
    
    # 创建 ChromaDB 向量存储
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=_embedding,
        collection_name=collection_name,
        client_settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    return vector_store


def build_vector_store(text_content: str, collection_name: str = "knowledge_base") -> str:
    """
    构建向量存储：将文本内容切片并存入 ChromaDB
    
    Args:
        text_content: 长文本内容
        collection_name: 集合名称（默认为 "knowledge_base"）
        
    Returns:
        成功提示信息
    """
    if not text_content or not text_content.strip():
        return "⚠️ 文本内容为空，无法构建知识库"
    
    try:
        # 1. 获取 Embedding 实例
        embedding = _get_embedding_instance()
        
        # 2. 文本切片
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        chunks = text_splitter.split_text(text_content)
        
        if not chunks:
            return "⚠️ 文本切片后为空，无法构建知识库"
        
        # 3. 获取向量存储（如果已存在，会先清空再重建）
        # 注意：这里我们需要先删除旧的集合（如果存在）
        persist_directory = "./chroma_db"
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding,
            collection_name=collection_name,
            client_settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 清空现有数据（如果存在）
        try:
            vector_store.delete_collection()
        except:
            pass  # 如果集合不存在，忽略错误
        
        # 重新创建向量存储并添加文档
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embedding,
            persist_directory=persist_directory,
            collection_name=collection_name,
            client_settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 持久化
        vector_store.persist()
        
        return f"✅ 知识库构建完成！共处理 {len(chunks)} 个文本片段。"
        
    except Exception as e:
        error_msg = f"❌ 构建向量存储时出错: {str(e)}"
        st.error(error_msg)
        return error_msg


def query_vector_store(question: str, k: int = 3, collection_name: str = "knowledge_base") -> str:
    """
    查询向量存储：在 ChromaDB 中进行相似性搜索
    
    Args:
        question: 用户问题
        k: 返回最相关的 k 个文本片段（默认 3）
        collection_name: 集合名称（默认为 "knowledge_base"）
        
    Returns:
        合并后的相关文本片段（字符串）
    """
    if not question or not question.strip():
        return ""
    
    try:
        # 1. 获取 Embedding 实例
        embedding = _get_embedding_instance()
        
        # 2. 获取向量存储
        persist_directory = "./chroma_db"
        
        # 检查向量存储是否存在
        if not os.path.exists(persist_directory):
            return "⚠️ 知识库尚未构建，请先上传文档构建知识库"
        
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding,
            collection_name=collection_name,
            client_settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 3. 相似性搜索
        results = vector_store.similarity_search(question, k=k)
        
        if not results:
            return "⚠️ 未找到相关文档片段"
        
        # 4. 合并结果
        relevant_texts = [doc.page_content for doc in results]
        merged_text = "\n\n---\n\n".join(relevant_texts)
        
        return merged_text
        
    except Exception as e:
        error_msg = f"❌ 查询向量存储时出错: {str(e)}"
        st.error(error_msg)
        return ""

