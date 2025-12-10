import streamlit as st
from core.llm_client import get_client  # 确保你的 core 文件夹里有这个

# --- 1. 页面基本配置 ---
# st.set_page_config 已在 main.py 配置过，这里不再重复，否则会报错

# --- 2. 初始化核心变量 ---
# 只有当它不存在时才创建，保证页面刷新时不会无故清空，但也不会乱保留
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 定义最纯粹的 System Prompt ---
# 没有任何范例，只有强制指令。AI 只要这一句就够了。
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
    你是一位严谨的工业维修专家。
    你的任务是根据用户的故障描述，直接输出维修排查清单。
    
    【回答规则】：
    1. 必须使用 Markdown 列表格式。
    2. 禁止反问用户，禁止说“请提供更多信息”。
    3. 如果信息不全，请列出最常见情况的通用排查步骤。
    4. 风格要干练、技术化，不要客套。
    """
}

# --- 4. 核心功能函数：处理对话 ---
def handle_chat(user_input):
    """
    处理用户输入的核心逻辑：
    1. 显示用户的话
    2. 把话存进历史
    3. 调用 AI
    4. 显示 AI 的话并存进历史
    """
    # A. 界面显示用户输入
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # B. 存入历史
    st.session_state.messages.append({"role": "user", "content": user_input})

    # C. 呼叫 AI
    with st.chat_message("assistant"):
        client = get_client()
        
        # 构造发送给 AI 的消息列表：[系统人设] + [历史记录]
        # 这样 AI 既知道自己是谁，也知道之前聊了什么
        api_messages = [SYSTEM_PROMPT] + st.session_state.messages
        
        # 发起请求
        response = client.chat.completions.create(
            model="glm-4-flash", # 确保你 core 里改了智谱的 key
            messages=api_messages,
            stream=True,
            temperature=0.1 # 低温，保证不乱发挥
        )
        
        # D. 流式输出并获取完整回复
        full_response = st.write_stream(response)
    
    # E. 把 AI 的回复存入历史
    st.session_state.messages.append({"role": "assistant", "content": full_response})


# --- 5. 侧边栏功能 ---
with st.sidebar:
    st.header("🛠️ 维修工具箱")
    
    # 上传文件功能（保留界面，暂不接入逻辑，防止报错）
    st.file_uploader("上传故障日志/图片", type=["png", "jpg", "pdf"])
    
    st.divider()
    
    # === 关键功能：强制清空按钮 ===
    if st.button("🗑️ 清空对话 / 重置", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun() # 立即刷新页面


# --- 6. 主界面布局 ---
st.title("🏭 工业人工智能大脑")
st.caption("Industrial Fault Diagnosis Expert System")

# === 快捷指令区（核心修复点） ===
# 这里的逻辑是：点击按钮 -> 1.清空旧历史 -> 2.自动发送新指令
st.markdown("##### ⚡ 快速诊断通道")
col1, col2, col3, col4 = st.columns(4)

# 定义按钮点击后的动作
def quick_action(prompt):
    st.session_state.messages = [] # 第一步：先失忆，防止串台
    handle_chat(prompt)            # 第二步：发送指定指令

# 按钮 1
if col1.button("伺服电机故障", use_container_width=True):
    quick_action("我的设备出现了【伺服电机故障】。请详细列出：硬件检查、电气检查、参数设置三方面的排查步骤。")

# 按钮 2
if col2.button("通讯超时", use_container_width=True):
    quick_action("我的设备出现了【PLC通讯超时】。请详细列出：物理连接、网络配置、干扰排查三方面的排查步骤。")

# 按钮 3
if col3.button("ABB机器人错误", use_container_width=True):
    quick_action("我的ABB机器人报错。请列出最常见的5个错误代码及其含义和解决办法。")

# 按钮 4
if col4.button("编码器异常", use_container_width=True):
    quick_action("我的设备报【编码器故障】。请列出排查步骤（线路、电池、机械安装）。")

st.divider()

# --- 7. 聊天记录回显区 ---
# 这一步是为了在页面刷新后，依然能看到之前的聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 8. 底部输入框 ---
# 允许用户自己打字问其他问题
if user_input := st.chat_input("请描述具体的故障现象..."):
    handle_chat(user_input)