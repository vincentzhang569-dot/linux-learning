import streamlit as st
from core.llm_client import get_client
from core.rag_bridge import build_vector_store, query_vector_store
import pdfplumber  # 记得确保安装了这个库：pip install pdfplumber

# --- 1. 核心变量初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge_base_ready" not in st.session_state:
    st.session_state.knowledge_base_ready = False  # 标记知识库是否已构建

# --- 2. 侧边栏：文件上传功能 (RAG 升级版) ---
with st.sidebar:
    st.header("📂 知识库挂载")
    st.caption("上传技术手册/维修文档，AI 将基于文档回答。")
    
    # === 侧边栏：文档上传区 ===
    uploaded_file = st.file_uploader("上传 PDF 文档", type=["pdf"])
    
    # 处理文件上传
    if uploaded_file is not None:
        # 定义最大页数限制 (保护 2G 内存服务器)
        MAX_PAGES = 50 
        
        try:
            # 检查是否已经处理过这个文件，防止重复计算
            if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
                
                # 1. 进度条组件
                progress_bar = st.progress(0, text="正在启动文档解析引擎...")
                text = ""
                
                with pdfplumber.open(uploaded_file) as pdf:
                    total_pages = len(pdf.pages)
                    # 如果页数太多，强制截断
                    process_pages = min(total_pages, MAX_PAGES)
                    
                    if total_pages > MAX_PAGES:
                        st.warning(f"⚠️ 文档过大 ({total_pages}页)，为防止服务器崩溃，仅读取前 {MAX_PAGES} 页。")
                    
                    # 2. 逐页读取并更新进度条
                    for i in range(process_pages):
                        page_text = pdf.pages[i].extract_text()
                        if page_text:
                            text += page_text + "\n"
                        
                        # 更新进度 (0% - 50%)
                        current_progress = int((i / process_pages) * 50)
                        progress_bar.progress(current_progress, text=f"正在读取第 {i+1}/{process_pages} 页...")
                
                # 3. 构建向量库 (耗时操作)
                if text:
                    progress_bar.progress(60, text="正在切分文本并构建向量索引 (这需要一点时间)...")
                    
                    # 调用 core 里的函数
                    result_msg = build_vector_store(text)
                    
                    # 完成
                    progress_bar.progress(100, text="✅ 处理完成！")
                    st.success(result_msg)
                    
                    # 记录状态
                    if result_msg.startswith("✅"):
                        st.session_state.knowledge_base_ready = True
                    else:
                        st.session_state.knowledge_base_ready = False
                    st.session_state.doc_content = text # (可选：存原文以便查看，如果内存紧张可注释掉这行)
                    st.session_state.last_uploaded = uploaded_file.name
                
        except Exception as e:
            st.error(f"文档读取失败: {e}")
            st.session_state.knowledge_base_ready = False
    else:
        # 如果用户移除文件，重置知识库状态
        st.session_state.knowledge_base_ready = False

    st.divider()
    
    # 强制清空按钮
    if st.button("🗑️ 清空对话 / 重置", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 3. 基础 System Prompt 模板 ---
base_system_prompt = """
你是一位工业维修专家。
请基于以下【参考资料】回答用户问题。如果资料中没有答案，请使用你的专业知识补充，但要说明"资料中未提及"。
"""


# --- 4. 主界面布局 ---
st.title("🏭 工业人工智能大脑")

# === 关键修复：先显示历史记录，再处理新输入 ===
# (把这段代码挪到上面，解决了“回答两次”的 BUG)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. 处理聊天的函数 ---
def handle_chat(user_input):
    # 1. 既然上面已经显示了历史，这里只需要显示"新的一轮"
    # A. 显示用户输入
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # B. 显示 AI 回复
    with st.chat_message("assistant"):
        # 2. RAG 查询：从向量库中检索相关上下文
        context = ""
        if st.session_state.knowledge_base_ready:
            context = query_vector_store(user_input, k=3)
        
        # 3. 构建动态 System Prompt
        if context:
            final_system_content = f"""
{base_system_prompt}

【参考资料】：
{context}
"""
        else:
            final_system_content = base_system_prompt
        
        system_prompt = {"role": "system", "content": final_system_content}
        
        # 4. 调用 AI
        client = get_client()
        # 构造消息：系统设定 + 历史记录
        api_messages = [system_prompt] + st.session_state.messages
        
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=api_messages,
            stream=True,
            temperature=0.1
        )
        full_response = st.write_stream(response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})


# --- 6. 快捷按钮区 ---
st.markdown("##### ⚡ 快速诊断通道")
col1, col2, col3, col4 = st.columns(4)

def quick_action(prompt):
    # 强制清空历史，防止串台
    st.session_state.messages = []
    # 强制刷新页面，让上面的历史记录区清空
    # 但为了能执行 handle_chat，我们需要一点小技巧：
    # 直接在这里调用 handle_chat，因为 session_state 已经清空，上面循环不会打印旧的
    handle_chat(prompt)
    # 注意：这里不需要 rerun，因为 handle_chat 会实时画出来

if col1.button("伺服电机故障", use_container_width=True):
    quick_action("我的设备出现了【伺服电机故障】。请详细列出：硬件检查、电气检查、参数设置三方面的排查步骤。")

if col2.button("通讯超时", use_container_width=True):
    quick_action("我的设备出现了【PLC通讯超时】。请详细列出：物理连接、网络配置、干扰排查三方面的排查步骤。")

if col3.button("ABB机器人错误", use_container_width=True):
    quick_action("我的ABB机器人报错。请列出最常见的5个错误代码及其含义和解决办法。")

if col4.button("编码器异常", use_container_width=True):
    quick_action("我的设备报【编码器故障】。请列出排查步骤（线路、电池、机械安装）。")

# --- 7. 底部输入框 ---
if user_input := st.chat_input("请输入具体故障现象，或上传文档后提问..."):
    handle_chat(user_input)
