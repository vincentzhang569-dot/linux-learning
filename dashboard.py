import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 1. 页面基础配置 (只执行一次) ====================
st.set_page_config(
    page_title="工业物联网实时监控大屏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 样式：保持暗黑工业风
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #ffffff; font-family: 'Arial', sans-serif; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3f 100%);
        border: 2px solid; border-radius: 10px; padding: 15px;
        text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s;
    }
    .status-running { border-color: #00ff41; color: #00ff41; }
    .status-warning { border-color: #ffd700; color: #ffd700; }
    .status-error { border-color: #ff0000; color: #ff0000; }
    .robot-name { font-size: 18px; font-weight: bold; color: #fff; }
    .metric-value { font-size: 14px; color: #b0b0b0; margin-top: 5px;}
</style>
""", unsafe_allow_html=True)

# ==================== 2. 核心：智能数据模拟引擎 ====================

ROBOTS = ['Robot_A01', 'Robot_B02', 'Robot_C03', 'Robot_D04', 'Robot_E05']

def get_status(temp, vib):
    """根据数值判断状态，实现状态自动流转"""
    if temp > 85 or vib > 6:
        return 'Error'
    elif temp > 75 or vib > 4:
        return 'Warning'
    else:
        return 'Running'

def init_simulation_data():
    """初始化历史数据：控制开局节奏，不要全崩"""
    now = datetime.now()
    data = []
    
    for idx, robot in enumerate(ROBOTS):
        # --- 真实感修改：差异化初始状态 ---
        # 前3台机器 (A, B, C) 状态良好
        if idx < 3:
            base_temp = np.random.uniform(45, 55) # 正常温度
            base_vib = np.random.uniform(0.2, 0.5)
        # 后2台机器 (D, E) 有点小毛病
        else:
            base_temp = np.random.uniform(70, 78) # 偏高，接近 Warning
            base_vib = np.random.uniform(2.0, 3.5)

        current_temp = base_temp
        current_vib = base_vib
        
        # 生成过去60秒的数据
        for i in range(60): 
            timestamp = now - timedelta(seconds=(60-i))
            
            # 温度惯性波动
            current_temp += np.random.normal(0, 0.5)
            # 振动波动
            current_vib = max(0, base_vib + np.random.normal(0, 0.2))
            
            status = get_status(current_temp, current_vib)
            
            data.append({
                'Timestamp': timestamp,
                'Robot_ID': robot,
                'Motor_Temperature': current_temp,
                'Vibration_Level': current_vib,
                'Status': status
            })
    
    return pd.DataFrame(data)

def generate_next_step(current_df):
    """生成下一秒数据：加入【自愈】和【散热】逻辑"""
    last_timestamp = current_df['Timestamp'].max()
    new_timestamp = last_timestamp + timedelta(seconds=1)
    
    new_rows = []
    latest_readings = current_df.sort_values('Timestamp').groupby('Robot_ID').last()
    
    for robot in ROBOTS:
        last_row = latest_readings.loc[robot]
        last_temp = last_row['Motor_Temperature']
        last_vib = last_row['Vibration_Level']
        
        # === 1. 温度逻辑：加入自动温控模拟 ===
        change = np.random.normal(0, 0.4) # 默认自然波动
        
        if last_temp > 85:
            # 触发强力散热：温度过高时，大概率下降
            change = -1.5 + np.random.normal(0, 0.2)
        elif last_temp > 75:
            # 触发温和散热
            change = -0.5 + np.random.normal(0, 0.2)
        elif last_temp < 40:
            # 机器预热
            change = 0.8
            
        new_temp = last_temp + change
        
        # === 2. 振动逻辑：尖峰后迅速回落 ===
        if last_vib > 5:
            # 如果之前震动很大，模拟急停或稳定下来，迅速降低
            new_vib = last_vib * 0.6 
        else:
            # 1% 概率产生一个小冲击
            if np.random.random() < 0.01:
                new_vib = last_vib + np.random.uniform(2, 4)
            else:
                # 正常微小波动
                base_vib = 0.5 if 'A' in robot or 'B' in robot else 2.0 # 坏机器底噪大一点
                new_vib = base_vib + np.random.normal(0, 0.2)
        
        new_vib = max(0, new_vib) # 不能小于0

        # === 3. 状态自动更新 (关键：根据新数值重新判定) ===
        new_status = get_status(new_temp, new_vib)
            
        new_rows.append({
            'Timestamp': new_timestamp,
            'Robot_ID': robot,
            'Motor_Temperature': new_temp,
            'Vibration_Level': new_vib,
            'Status': new_status
        })
        
    return pd.DataFrame(new_rows)

# ==================== 3. 状态管理 ====================

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = init_simulation_data()

# 侧边栏
st.sidebar.markdown("### ⚙️ 监控台设置")
# 默认 2秒刷新一次，避免太快导致视觉疲劳
refresh_rate = st.sidebar.slider('数据刷新频率 (秒)', 1.0, 5.0, 2.0) 
auto_refresh = st.sidebar.checkbox('🔴 保持实时连接', value=True)

# 更新数据逻辑
if auto_refresh:
    new_data = generate_next_step(st.session_state.sensor_data)
    st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_data], ignore_index=True)
    # 保持最近 500 行，防止内存溢出
    if len(st.session_state.sensor_data) > 1000:
        st.session_state.sensor_data = st.session_state.sensor_data.iloc[-1000:]

df = st.session_state.sensor_data

# ==================== 4. 界面布局 ====================

# 标题栏
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("## 🏭 数字化产线监控中心 (Live)")
with col2:
    st.markdown(f"<div style='text-align:right; color:#00d4ff; font-family:monospace; font-size:20px'>{datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

st.markdown("---")

# 上半部分：状态卡片 (Status Cards)
latest = df.sort_values('Timestamp').groupby('Robot_ID').last().reset_index()
cols = st.columns(5)

for idx, row in latest.iterrows():
    status = row['Status']
    # 样式映射
    if status == 'Running':
        s_cls, icon = 'status-running', '✅'
    elif status == 'Warning':
        s_cls, icon = 'status-warning', '⚠️'
    else:
        s_cls, icon = 'status-error', '🚨'
        
    with cols[idx]:
        st.markdown(f"""
        <div class="metric-card {s_cls}">
            <div class="robot-name">{row['Robot_ID']}</div>
            <div style="font-size: 24px; margin: 10px 0;">{icon} {status}</div>
            <div class="metric-value">
                🌡️ {row['Motor_Temperature']:.1f}°C <br>
                📈 {row['Vibration_Level']:.2f} mm/s
            </div>
        </div>
        """, unsafe_allow_html=True)

# 下半部分：图表区 (Charts) - 重点解决闪烁问题
st.markdown("### 📊 关键指标实时趋势")

# 准备图表数据（只取最近 60 个点，保证时间窗口平滑）
chart_data = df[df['Robot_ID'].isin(ROBOTS)].tail(300) # 5个机器人 * 60点

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, 
                    subplot_titles=("核心电机温度 (°C)", "机械振动频率 (mm/s)"))

# 绘制线条
colors = ['#00d4ff', '#00ff41', '#ffd700', '#ff00ff', '#ffffff']
for i, robot in enumerate(ROBOTS):
    r_data = chart_data[chart_data['Robot_ID'] == robot]
    
    # 温度线
    fig.add_trace(go.Scatter(
        x=r_data['Timestamp'], y=r_data['Motor_Temperature'],
        mode='lines', name=f'{robot} Temp',
        line=dict(width=2, color=colors[i]), showlegend=False
    ), row=1, col=1)
    
    # 振动线
    fig.add_trace(go.Scatter(
        x=r_data['Timestamp'], y=r_data['Vibration_Level'],
        mode='lines', name=f'{robot} Vib',
        line=dict(width=1.5, color=colors[i]), showlegend=True # 只在这里显示图例
    ), row=2, col=1)

# === 关键修改：固定坐标轴范围，防止画面跳动 (Anti-Flicker) ===
fig.update_layout(
    height=450,
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(255,255,255,0.05)',
    font=dict(color='white'),
    legend=dict(orientation="h", y=-0.2),
    # 禁用 Plotly 的一些动态效果以提升性能
    hovermode="x unified"
)

# 锁死 Y 轴范围，这样格子就不会动了，只有线在跑
fig.update_yaxes(range=[30, 100], row=1, col=1, gridcolor='rgba(255,255,255,0.1)') # 温度固定 30-100
fig.update_yaxes(range=[0, 10], row=2, col=1, gridcolor='rgba(255,255,255,0.1)')   # 振动固定 0-10
fig.update_xaxes(showgrid=False)

# 渲染图表
st.plotly_chart(fig, use_container_width=True, key="live_chart") # 加key防止重绘丢失状态

# 自动刷新触发器
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
