import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="工业智脑综合管理平台", # 保持你的标题要求
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 1. 核心：实时数据模拟引擎 ====================

# 初始化机器人配置
ROBOTS = ['Robot_A01', 'Robot_B02', 'Robot_C03', 'Robot_D04', 'Robot_E05']

def init_simulation_data():
    """初始化历史数据"""
    now = datetime.now()
    data = []
    
    for idx, robot in enumerate(ROBOTS):
        # 保持之前的逻辑：前3台状态好，后2台稍差
        if idx < 3:
            base_temp = np.random.uniform(45, 55)
            base_vib = np.random.uniform(0.2, 0.4)
        else:
            base_temp = np.random.uniform(65, 75) 
            base_vib = np.random.uniform(0.5, 1.5)

        base_load = np.random.uniform(5, 8)
        
        for i in range(100):
            timestamp = now - timedelta(seconds=(100-i)*2)
            temp = base_temp + np.random.normal(0, 1.0)
            vib = base_vib + np.random.normal(0, 0.1)
            load = base_load + np.random.normal(0, 0.2) + np.sin(i/10)*2
            
            status = 'Running'
            if temp > 80 or vib > 5: status = 'Error'
            elif temp > 70 or vib > 3: status = 'Warning'
            
            data.append({
                'Timestamp': timestamp,
                'Robot_ID': robot,
                'Motor_Temperature': temp,
                'Vibration_Level': max(0, vib),
                'Current_Load': max(0, load),
                'Status': status
            })
    
    return pd.DataFrame(data)

def generate_next_step(current_df):
    """生成下一秒的实时数据"""
    last_timestamp = current_df['Timestamp'].max()
    new_timestamp = last_timestamp + timedelta(seconds=2)
    
    new_rows = []
    latest_readings = current_df.sort_values('Timestamp').groupby('Robot_ID').last()
    
    for robot in ROBOTS:
        last_row = latest_readings.loc[robot]
        current_temp = last_row['Motor_Temperature']
        current_vib = last_row['Vibration_Level']
        
        # 保持之前的自愈逻辑
        change = np.random.normal(0, 0.4) 
        if current_temp > 82: change -= 1.2
        elif current_temp > 72: change -= 0.6
        elif current_temp < 40: change += 0.5
            
        new_temp = current_temp + change
        
        if current_vib > 4: new_vib = current_vib * 0.8
        elif np.random.random() < 0.01: new_vib = current_vib + np.random.uniform(2, 3)
        else: new_vib = current_vib * 0.95 + np.random.normal(0.2, 0.05)
            
        seconds = new_timestamp.timestamp()
        new_load = 6 + 3 * np.sin(seconds / 20) + np.random.normal(0, 0.1)
        
        status = 'Running'
        if new_temp > 80 or new_vib > 5: status = 'Error'
        elif new_temp > 70 or new_vib > 3: status = 'Warning'
            
        new_rows.append({
            'Timestamp': new_timestamp,
            'Robot_ID': robot,
            'Motor_Temperature': new_temp,
            'Vibration_Level': max(0, new_vib),
            'Current_Load': max(0, new_load),
            'Status': status
        })
        
    return pd.DataFrame(new_rows)

# ==================== 2. 状态管理 ====================

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = init_simulation_data()
    st.session_state.is_running = True

# 侧边栏控制区
st.sidebar.markdown("### 🎮 模拟器控制台")
auto_refresh = st.sidebar.toggle('⏱️ 开启实时数据流', value=True)

# === 关键修改在这里：默认值从 1.0 改成了 3.0 ===
refresh_rate = st.sidebar.slider('刷新频率 (秒)', 0.5, 5.0, 3.0)

if auto_refresh:
    new_data = generate_next_step(st.session_state.sensor_data)
    st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_data], ignore_index=True)
    if len(st.session_state.sensor_data) > 2500:
        st.session_state.sensor_data = st.session_state.sensor_data.iloc[-2500:]

df = st.session_state.sensor_data

# ==================== 3. 界面渲染 ====================

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #ffffff; font-family: 'Arial', sans-serif; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3f 100%);
        border: 2px solid; border-radius: 10px; padding: 15px;
        text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }
    .status-running { border-color: #00ff41; box-shadow: 0 0 15px rgba(0, 255, 65, 0.2); }
    .status-warning { border-color: #ffd700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.2); }
    .status-error { border-color: #ff0000; box-shadow: 0 0 15px rgba(255, 0, 0, 0.2); }
    .robot-name { font-size: 18px; font-weight: bold; color: #fff; }
    .metric-value { font-size: 14px; color: #b0b0b0; }
</style>
""", unsafe_allow_html=True)

col_title, col_time = st.columns([3, 1])
with col_title:
    st.markdown("## 🏭 工业智脑综合管理平台 (Live Monitor)")
with col_time:
    st.markdown(f"<h3 style='text-align: right; color: #00d4ff;'>{datetime.now().strftime('%H:%M:%S')}</h3>", unsafe_allow_html=True)

st.markdown("---")

st.markdown("### 📊 实时设备状态")
latest_data = df.sort_values('Timestamp').groupby('Robot_ID').last().reset_index()

cols = st.columns(5)
for idx, row in latest_data.iterrows():
    col_idx = idx % 5
    status = row['Status']
    
    if status == 'Running':
        s_class, s_color, s_icon = 'status-running', '#00ff41', '✓'
    elif status == 'Warning':
        s_class, s_color, s_icon = 'status-warning', '#ffd700', '⚠'
    else:
        s_class, s_color, s_icon = 'status-error', '#ff0000', '✕'
    
    with cols[col_idx]:
        st.markdown(f"""
        <div class="metric-card {s_class}">
            <div class="robot-name">{row['Robot_ID']}</div>
            <div style="font-size: 20px; font-weight: bold; color: {s_color}; margin: 10px 0;">
                {s_icon} {status}
            </div>
            <div class="metric-value">温度: {row['Motor_Temperature']:.1f}°C</div>
            <div class="metric-value">振动: {row['Vibration_Level']:.2f} mm/s</div>
            <div class="metric-value">负载: {row['Current_Load']:.2f} A</div>
        </div>
        """, unsafe_allow_html=True)

col_chart, col_alert = st.columns([2, 1])

with col_chart:
    st.markdown("### 📈 实时趋势监控")
    selected_robot = st.sidebar.selectbox("选择监控对象", ROBOTS, index=0)
    
    robot_df = df[df['Robot_ID'] == selected_robot].tail(100)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, row_heights=[0.5, 0.5])
    
    fig.add_trace(go.Scatter(
        x=robot_df['Timestamp'], y=robot_df['Motor_Temperature'],
        mode='lines', name='温度', line=dict(color='#00d4ff', width=2),
        fill='tozeroy', fillcolor='rgba(0, 212, 255, 0.1)'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=robot_df['Timestamp'], y=robot_df['Vibration_Level'],
        mode='lines', name='振动', line=dict(color='#00ff41', width=2),
        fill='tozeroy', fillcolor='rgba(0, 255, 65, 0.1)'
    ), row=2, col=1)
    
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=1, col=1, annotation_text="高温阈值")
    fig.add_hline(y=5, line_dash="dash", line_color="red", row=2, col=1, annotation_text="振动阈值")

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        font=dict(color='white')
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    
    st.plotly_chart(fig, use_container_width=True)

with col_alert:
    st.markdown("### ⚠️ 实时预警日志")
    alerts = df[df['Status'].isin(['Warning', 'Error'])].sort_values('Timestamp', ascending=False).head(10)
    
    if not alerts.empty:
        for _, row in alerts.iterrows():
            color = "#ff4b4b" if row['Status'] == 'Error' else "#ffa421"
            bg_color = "rgba(255, 75, 75, 0.1)" if row['Status'] == 'Error' else "rgba(255, 164, 33, 0.1)"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #fff; font-weight: bold;">{row['Robot_ID']}</span>
                    <span style="color: #ccc; font-size: 12px;">{row['Timestamp'].strftime('%H:%M:%S')}</span>
                </div>
                <div style="color: {color}; margin-top: 4px; font-size: 14px;">
                    {row['Status']}: Temp {row['Motor_Temperature']:.1f}°C | Vib {row['Vibration_Level']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ 系统运行平稳，暂无异常")

# ==================== 4. 自动刷新逻辑 ====================

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()