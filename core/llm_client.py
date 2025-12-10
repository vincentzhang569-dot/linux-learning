# core/llm_client.py

import streamlit as st

from openai import OpenAI

# 硅基流动基础配置

SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

# 你在 app.py 里用到的视觉模型名，保持一致

SILICONFLOW_MODEL = "Qwen/Qwen2-VL-72B-Instruct"

@st.cache_resource

def get_client() -> OpenAI:

    """

    获取硅基流动的 OpenAI 兼容客户端。

    - 自动从 st.secrets 读取 SILICONFLOW_API_KEY

    - 创建后用 cache_resource 缓存（整个进程只建一次连接）

    """

    try:

        api_key = st.secrets["SILICONFLOW_API_KEY"]

    except (FileNotFoundError, KeyError, AttributeError):

        st.error("⚠️ 未找到 API Key，请在 .streamlit/secrets.toml 中配置 SILICONFLOW_API_KEY")

        st.stop()

    client = OpenAI(

        api_key=api_key,

        base_url=SILICONFLOW_BASE_URL

    )

    return client

