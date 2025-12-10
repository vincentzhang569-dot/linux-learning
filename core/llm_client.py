# core/llm_client.py

import streamlit as st

from openai import OpenAI

# 1. 改成智谱的官方地址（OpenAI兼容版）

ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# 改成智谱的"闪电"模型，速度极快！

MODEL_NAME = "glm-4-flash"

@st.cache_resource

def get_client() -> OpenAI:

    # 2. 读取新的 Key

    try:

        api_key = st.secrets["ZHIPU_API_KEY"]

    except Exception:

        st.error("⚠️ 未找到智谱 API Key")

        st.stop()

    # 3. 创建客户端

    client = OpenAI(

        api_key=api_key,

        base_url=ZHIPU_BASE_URL

    )

    return client

