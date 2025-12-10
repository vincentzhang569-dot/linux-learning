import streamlit as st
from core.llm_client import get_client
import pdfplumber  # 记得确保安装了这个库：pip install pdfplumber

# --- 1. 核心变量初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "context_content" not in st.session_state:
    st.session_state.context_content = ""  # 用于存储上传文档的内容

# --- 2. 侧边栏：文件上传功能 (RAG 简易版) ---
with st.sidebar:
    st.header("📂 知识库挂载")
    st.caption("上传技术手册/维修文档，AI 将基于文档回答。")
    
    uploaded_file = st.file_uploader("上传 PDF 文档", type=["pdf"])
    
    # 处理文件上传逻辑
    if uploaded_file is not None:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                # 提取所有页面的文本
                all_text = ""
                for page in pdf.pages:
                    all_text += page.extract_text() + "\n"
                
                st.session_state.context_content = all_text
                st.success(f"✅ 文档已加载！包含 {len(pdf.pages)} 页内容。")
        except Exception as e:
            st.error(f"❌ 解析失败: {e}")
    else:
        # 如果用户移除文件，清空上下文
        st.session_state.context_content = ""

    st.divider()
    
    # 强制清空按钮
    if st.button("🗑️ 清空对话 / 重置", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 3. 定义动态 System Prompt ---
# 如果有文档，就把文档塞进脑子里；如果没有，就只用基础人设
base_system_prompt = """
你是一位严谨的工业维修专家。
任务：根据用户的故障描述，直接输出维修排查清单。
规则：Markdown 列表格式，禁止反问，禁止客套。
"""

if st.session_state.context_content:
    # RAG 模式：让 AI 基于文档回答
    final_system_content = f"""
    {base_system_prompt}
    
    【重要】：用户已上传技术参考文档，内容如下：
    ---
    {st.session_state.context_content[:50000]} 
    ---
    请优先依据上述文档内容进行故障分析。
    """
    # 注意：这里截取前5万字防止超长，GLM-4-Flash 支持长文本，一般够用
else:
    # 普通模式
    final_system_content = base_system_prompt

SYSTEM_PROMPT = {"role": "system", "content": final_system_content}


# --- 4. 主界面布局 ---
st.title("🏭 工业人工智能大脑")

# === 关键修复：先显示历史记录，再处理新输入 ===
# (把这段代码挪到上面，解决了“回答两次”的 BUG)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. 处理聊天的函数 ---
def handle_chat(user_input):
    # 1. 既然上面已经显示了历史，这里只需要显示“新的一轮”
    # A. 显示用户输入
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # B. 显示 AI 回复
    with st.chat_message("assistant"):
        client = get_client()
        # 构造消息：系统设定 + 历史记录
        api_messages = [SYSTEM_PROMPT] + st.session_state.messages
        
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
