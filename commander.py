import streamlit as st
import pandas as pd
import json
import time
import re
import ast
from openai import OpenAI
from robot_controller import RobotController

# --- 1. 自动加载配置 ---
try:
    api_key = st.secrets["SILICONFLOW_API_KEY"]
    base_url = "https://api.siliconflow.cn/v1"
    # 🔥 核心更换：改用 Coder 模型，它对 JSON 格式的执行力极强，极少犯错
    model_name = "Qwen/Qwen2.5-Coder-32B-Instruct" 
except:
    # API Key 未配置时的占位符（仅用于开发环境，上传时请注释或删除）
    api_key = None
    base_url = ""

client = OpenAI(api_key=api_key, base_url=base_url)

# --- 2. 初始化控制器 ---
if "controller" not in st.session_state:
    st.session_state.controller = RobotController(num_robots=5)
controller = st.session_state.controller

# --- 3. CSS 样式 ---
st.markdown("""
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
""", unsafe_allow_html=True)

# --- 4. 工具定义 ---
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
                    "target_speed": {"type": "integer"}
                }, 
                "required": ["robot_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emergency_stop",
            "description": "紧急停止机器人。",
            "parameters": {"type": "object", "properties": {"robot_id": {"type": "integer"}}, "required": ["robot_id"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_speed",
            "description": "调整速度。",
            "parameters": {"type": "object", "properties": {"robot_id": {"type": "integer"}, "speed": {"type": "integer"}}, "required": ["robot_id", "speed"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reset_system",
            "description": "重置系统。",
            "parameters": {"type": "object", "properties": {"robot_id": {"type": "integer"}}, "required": ["robot_id"]}
        }
    }
]

# --- 5. 执行逻辑 ---
def execute_command(func_name, args, status_container):
    status_container.write(f"⚙️ **执行**: `{func_name}` | `{args}`")
    
    if isinstance(args, str):
        try: args = json.loads(args.replace("'", '"'))
        except: 
            try: args = ast.literal_eval(args)
            except: pass

    try:
        if hasattr(controller, func_name):
            function_to_call = getattr(controller, func_name)
            return function_to_call(**args)
        else:
            return {"success": False, "message": f"函数不存在"}
    except Exception as e:
        return {"success": False, "message": f"崩溃: {str(e)}"}

# --- 6. 界面布局 ---
st.markdown("### 🎮 工业 AI 指挥中枢")

status_dict = controller.get_all_status()
cols = st.columns(len(status_dict))
for idx, (r_id, data) in enumerate(status_dict.items()):
    with cols[idx]:
        status_color = "status-running"
        icon = "🟢"
        if data['status'] == 'Stopped': status_color = "status-stopped"; icon = "🟡"
        elif data['status'] == 'Emergency_Stop': status_color = "status-emergency"; icon = "🚨"
        
        st.markdown(f"""
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
        """, unsafe_allow_html=True)

st.divider()

# --- 7. 聊天逻辑 ---
if "cmd_messages" not in st.session_state:
    st.session_state.cmd_messages = [{
        "role": "system", 
        "content": """你是一个工业控制程序。
        1. 必须优先使用 Function Calling (工具调用)。
        2. 如果无法使用工具，请直接输出 JSON 格式的指令，例如：
           {"name": "startup_system", "arguments": {"robot_id": 1, "target_speed": 80}}
        3. 严禁废话，严禁 Markdown，只输出 JSON。
        """
    }]

# === 🔥 核心修改：移除所有隐藏逻辑，所见即所得 ===
for msg in st.session_state.cmd_messages:
    if msg["role"] == "user":
        with st.chat_message("user"): st.write(msg["content"])
    elif msg["role"] == "assistant":
        # 不管是不是代码，全部显示出来！绝不留白！
        with st.chat_message("assistant"):
            content = str(msg["content"])
            if "{" in content:
                st.code(content, language="json")
            else:
                st.write(content)

if prompt := st.chat_input("💬 下达指令..."):
    st.session_state.cmd_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.status("🧠 Agent 正在处理...", expanded=True) as status:
        try:
            response = client.chat.completions.create(
                model=model_name, messages=st.session_state.cmd_messages, tools=tools, tool_choice="auto"
            )
            response_message = response.choices[0].message
            content_text = response_message.content or ""
            tool_calls = response_message.tool_calls
            
            executed_any = False
            
            # A. 标准工具调用 (Coder模型通常走这里)
            if tool_calls:
                st.session_state.cmd_messages.append(response_message.model_dump())
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    result = execute_command(func_name, args, status)
                    
                    # 记录结果
                    st.session_state.cmd_messages.append({
                        "tool_call_id": tool_call.id, "role": "tool", "name": func_name, 
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                executed_any = True

            # B. 文本补救 (如果Coder模型偶尔抽风发了文本JSON)
            elif "{" in content_text:
                # 简单粗暴提取 JSON
                try:
                    # 寻找第一个 { 和 最后一个 }
                    start = content_text.find("{")
                    end = content_text.rfind("}") + 1
                    json_str = content_text[start:end]
                    
                    # 尝试解析
                    try: obj = json.loads(json_str)
                    except: obj = ast.literal_eval(json_str) # 容错单引号
                    
                    if isinstance(obj, dict) and "name" in obj:
                        func_name = obj["name"]
                        args = obj.get("arguments", {})
                        result = execute_command(func_name, args, status)
                        executed_any = True
                        st.session_state.cmd_messages.append({"role": "assistant", "content": content_text})
                except:
                    # 解析失败，直接显示原文
                    st.session_state.cmd_messages.append({"role": "assistant", "content": content_text})

            # === 只要执行了，就强制刷新 ===
            if executed_any:
                status.update(label="✅ 指令已送达底层", state="complete", expanded=False)
                
                # 不再让 AI 生成总结废话，直接显示系统提示
                with st.chat_message("assistant"):
                    st.success("✅ 操作已执行，正在同步状态...")
                
                # 存一个占位符防止下次加载报错
                st.session_state.cmd_messages.append({"role": "assistant", "content": "✅ 操作执行完毕。"})
                
                time.sleep(0.5)
                st.rerun()
            else:
                # 没执行动作，直接把 AI 的回复（哪怕是废话）显示出来
                status.update(label="💬 消息", state="complete", expanded=False)
                with st.chat_message("assistant"): st.write(content_text)
                st.session_state.cmd_messages.append({"role": "assistant", "content": content_text})

        except Exception as e:
            status.update(label="❌ 错误", state="error")
            st.error(f"Error: {e}")