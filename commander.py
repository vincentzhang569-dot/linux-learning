import json
import ast
import random
import time
import streamlit as st

from core.llm_client import get_client, MODEL_NAME
from core.tools import send_email_action
from robot_controller import RobotController

# --- 1. 初始化全局资源 ---
client = get_client()
if "controller" not in st.session_state:
    st.session_state.controller = RobotController(num_robots=5)
if "has_alerted" not in st.session_state:
    st.session_state.has_alerted = False
controller = st.session_state.controller

# --- 2. CSS 样式 ---
st.markdown(
    """
    <style>
    .robot-card {background-color: #262730; border: 1px solid #464b5d; border-radius: 10px; padding: 15px; margin-bottom: 10px;}
    .badge {padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white;}
    .status-running {background-color: #00C853;}
    .status-stopped {background-color: #FFAB00; color: black;}
    .status-emergency {background-color: #D50000; animation: pulse 1s infinite;}
    @keyframes pulse {0%{opacity:1;} 50%{opacity:0.5;} 100%{opacity:1;}}
    .metric-value {font-size: 24px; font-weight: bold; color: #FAFAFA;}
    .metric-label {font-size: 12px; color: #B0B0B0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. 工具定义（保留 AI 指挥官的指令功能） ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "startup_system",
            "description": "一键启动机器人(自动重置+设速度)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "robot_id": {"type": "integer"},
                    "target_speed": {"type": "integer"},
                },
                "required": ["robot_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "emergency_stop",
            "description": "紧急停止机器人。",
            "parameters": {
                "type": "object",
                "properties": {"robot_id": {"type": "integer"}},
                "required": ["robot_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_speed",
            "description": "调整速度。",
            "parameters": {
                "type": "object",
                "properties": {"robot_id": {"type": "integer"}, "speed": {"type": "integer"}},
                "required": ["robot_id", "speed"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_system",
            "description": "重置系统。",
            "parameters": {
                "type": "object",
                "properties": {"robot_id": {"type": "integer"}},
                "required": ["robot_id"],
            },
        },
    },
]


# --- 4. 执行底层指令 ---
def execute_command(func_name, args, status_container):
    status_container.write(f"⚙️ **执行**: `{func_name}` | `{args}`")

    if isinstance(args, str):
        try:
            args = json.loads(args.replace("'", '"'))
        except Exception:
            try:
                args = ast.literal_eval(args)
            except Exception:
                pass

    try:
        if hasattr(controller, func_name):
            function_to_call = getattr(controller, func_name)
            return function_to_call(**args)
        return {"success": False, "message": "函数不存在"}
    except Exception as e:
        return {"success": False, "message": f"崩溃: {str(e)}"}


# --- 5. 顶部：AI 指挥官对话区域（保留手动查询能力） ---
st.markdown("### 🎮 工业 AI 指挥中枢")

status_dict = controller.get_all_status()
cols = st.columns(len(status_dict))
for idx, (r_id, data) in enumerate(status_dict.items()):
    with cols[idx]:
        status_color = "status-running"
        icon = "🟢"
        if data["status"] == "Stopped":
            status_color = "status-stopped"
            icon = "🟡"
        elif data["status"] == "Emergency_Stop":
            status_color = "status-emergency"
            icon = "🚨"

        st.markdown(
            f"""
        <div class="robot-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="font-weight:bold;">🤖 #{data['id']}</span>
                <span class="badge {status_color}">{icon} {data['status']}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <div><div class="metric-label">TEMP</div><div class="metric-value" style="color:{'#FF5252' if data['temperature']>70 else '#FAFAFA'}">{data['temperature']}°C</div></div>
                <div><div class="metric-label">SPEED</div><div class="metric-value">{data['speed']}%</div></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

st.divider()

# --- 6. 聊天逻辑（仅用于手动查询和指令） ---
if "cmd_messages" not in st.session_state:
    st.session_state.cmd_messages = [
        {
            "role": "system",
            "content": """你是一个工业控制程序。
            1. 必须优先使用 Function Calling (工具调用)。
            2. 如果无法使用工具，请直接输出 JSON 格式的指令，例如：
               {"name": "startup_system", "arguments": {"robot_id": 1, "target_speed": 80}}
            3. 严禁废话，严禁 Markdown，只输出 JSON。
            """,
        }
    ]

for msg in st.session_state.cmd_messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            content = str(msg["content"])
            if "{" in content:
                st.code(content, language="json")
            else:
                st.write(content)

if prompt := st.chat_input("💬 下达指令..."):
    st.session_state.cmd_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.status("🧠 Agent 正在处理...", expanded=True) as status:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.cmd_messages,
                tools=tools,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            content_text = response_message.content or ""
            tool_calls = response_message.tool_calls

            executed_any = False

            if tool_calls:
                st.session_state.cmd_messages.append(response_message.model_dump())
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    result = execute_command(func_name, args, status)
                    st.session_state.cmd_messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                executed_any = True

            elif "{" in content_text:
                try:
                    start = content_text.find("{")
                    end = content_text.rfind("}") + 1
                    json_str = content_text[start:end]
                    try:
                        obj = json.loads(json_str)
                    except Exception:
                        obj = ast.literal_eval(json_str)

                    if isinstance(obj, dict) and "name" in obj:
                        func_name = obj["name"]
                        args = obj.get("arguments", {})
                        result = execute_command(func_name, args, status)
                        executed_any = True
                        st.session_state.cmd_messages.append(
                            {"role": "assistant", "content": content_text}
                        )
                except Exception:
                    st.session_state.cmd_messages.append(
                        {"role": "assistant", "content": content_text}
                    )

            if executed_any:
                status.update(label="✅ 指令已送达底层", state="complete", expanded=False)
                with st.chat_message("assistant"):
                    st.success("✅ 操作已执行，正在同步状态...")

                st.session_state.cmd_messages.append(
                    {"role": "assistant", "content": "✅ 操作执行完毕。"}
                )
                time.sleep(0.5)
                st.rerun()
            else:
                status.update(label="💬 消息", state="complete", expanded=False)
                with st.chat_message("assistant"):
                    st.write(content_text)
                st.session_state.cmd_messages.append(
                    {"role": "assistant", "content": content_text}
                )

        except Exception as e:
            status.update(label="❌ 错误", state="error")
            st.error(f"Error: {e}")

st.divider()

# --- 7. 实时数据监控 + 自动报警 ---
st.markdown("### 📡 实时数据监控面板")
toggle_on = st.toggle("启动实时数据流模拟", value=False)

if toggle_on:
    current_temp = random.uniform(80, 120)
    temp_placeholder = st.empty()
    alert_placeholder = st.empty()

    # 显示当前温度，>100 以红色强调
    if current_temp > 100:
        temp_placeholder.metric("1号机组温度", f"{current_temp:.1f} °C", delta="高温", delta_color="inverse")
    else:
        temp_placeholder.metric("1号机组温度", f"{current_temp:.1f} °C")

    # 自动触发报警逻辑
    if current_temp > 100 and not st.session_state.has_alerted:
        alert_msg = f"【自动警报】1号机组温度异常！当前值：{current_temp:.1f}°C，请立即处理！"
        try:
            send_email_action(alert_msg)
        except TypeError:
            # 兼容不同签名：尝试带 subject 形式
            send_email_action(subject="自动警报", content=alert_msg)
        alert_placeholder.error("检测到异常！报警邮件已自动发送！")
        st.session_state.has_alerted = True
    elif current_temp < 95:
        # 温度恢复，允许下次再次报警
        st.session_state.has_alerted = False

    # 模拟 2 秒刷新一次
    time.sleep(2)
    st.experimental_rerun()