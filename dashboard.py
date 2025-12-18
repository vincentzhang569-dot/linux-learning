import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 1. 页面基础配置 ====================
st.set_page_config(
    page_title="工业产线智控中心",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 保持你的工业风 CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #ffffff; font-family: 'Arial', sans-serif; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3f 100%);
        border: 1px solid #4a4a4a; border-radius: 8px; padding: 12px;
        text-align: center; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .status-running { border-left: 5px solid #00ff41; }
    .status-warning { border-left: 5px solid #ffd700; }
    .status-error { border-left: 5px solid #ff0000; }
    .robot-name { font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 5px;}
    .metric-value { font-size: 13px; color: #b0b0b0; }
    /* 隐藏 Streamlit 默认的右上角菜单，让它看起来更像独立软件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 2. 数据模拟引擎 (保持之前的逻辑) ====================

ROBOTS = ['Robot_A01', 'Robot_B02', 'Robot_C03', 'Robot_D04', 'Robot_E05']

def get_status(temp, vib):
    if temp > 85 or vib > 6: return 'Error'
    elif temp > 75 or vib > 4: return 'Warning'
    else: return 'Running'

def init_simulation_data():
    now = datetime.now()
    data = []
    for idx, robot in enumerate(ROBOTS):
        # 初始状态设置：前3好，后2差
        if idx < 3:
            base_temp, base_vib = 50, 0.5
        else:
            base_temp, base_vib = 72, 3.0 # 接近警戒线

        cur_t, cur_v = base_temp, base_vib
        for i in range(60): 
            ts = now - timedelta(seconds=(60-i))
            cur_t += np.random.normal(0, 0.5)
            cur_v = max(0, base_vib + np.random.normal(0, 0.2))
            data.append({
                'Timestamp': ts, 'Robot_ID': robot,
                'Motor_Temperature': cur_t, 'Vibration_Level': cur_v,
                'Status': get_status(cur_t, cur_v)
            })
    return pd.DataFrame(data)

def generate_next_step(current_df):
    last_timestamp = current_df['Timestamp'].max()
    new_timestamp = last_timestamp + timedelta(seconds=1)
    new_rows = []
    latest = current_df.sort_values('Timestamp').groupby('Robot_ID').last()
    
    for robot in ROBOTS:
        last = latest.loc[robot]
        lt, lv = last['Motor_Temperature'], last['Vibration_Level']
        
        # 物理模拟：散热与自愈
        change = np.random.normal(0, 0.4)
        if lt > 85: change = -1.2 # 强制散热
        elif lt < 40: change = 0.8
        
        nt = lt + change
        
        # 振动模拟
        if lv > 6: nv = lv * 0.7 # 故障后回落
        else:
             # 随机尖峰
             if np.random.random() < 0.02: nv = lv + 3
             else: nv = (0.5 if 'A' in robot or 'B' in robot else 2.5) + np.random.normal(0, 0.2)
        
        new_rows.append({
            'Timestamp': new_timestamp, 'Robot_ID': robot,
            'Motor_Temperature': nt, 'Vibration_Level': max(0, nv),
            'Status': get_status(nt, max(0, nv))
        })
    return pd.DataFrame(new_rows)

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = init_simulation_data()

# ==================== 3. 布局逻辑 ====================

# 标题
c1, c2 = st.columns([5,1])
with c1: st.markdown("## 🏭 产线核心设备温控中心")
with c2: st.markdown(f"<div style='text-align:right; color:#00d4ff; font-family:monospace; font-size:24px; padding-top:10px'>{datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# 状态卡片容器 (使用 empty 占位，虽然 Streamlit 每次都会重绘，但逻辑上分开)
status_container = st.container()
# 图表容器 (关键！把图表放在固定的容器里)
chart_container = st.empty()

# 侧边栏
with st.sidebar:
    st.markdown("### 控制面板")
    refresh_rate = st.slider('刷新周期 (秒)', 1.0, 3.0, 1.5)
    run = st.checkbox('实时数据接入', value=True)

# ==================== 4. 循环渲染逻辑 ====================

if run:
    # 1. 更新数据
    new_data = generate_next_step(st.session_state.sensor_data)
    st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_data], ignore_index=True).iloc[-1000:]
    df = st.session_state.sensor_data
    
    # 2. 渲染状态卡片 (Status Cards)
    with status_container:
        latest = df.sort_values('Timestamp').groupby('Robot_ID').last().reset_index()
        cols = st.columns(5)
        for i, row in latest.iterrows():
            stt = row['Status']
            s_cls = f"status-{stt.lower()}"
            icon = "🟢" if stt=='Running' else "🟡" if stt=='Warning' else "🔴"
            
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card {s_cls}">
                    <div class="robot-name">{row['Robot_ID']}</div>
                    <div style="font-size:18px; margin:5px 0;">{icon} {stt}</div>
                    <div class="metric-value">
                        {row['Motor_Temperature']:.1f}°C
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 3. 渲染图表 (重点解决 跳动 和 混淆 问题)
    with chart_container:
        # 使用 Subplots：5行1列，彻底分开每台机器
        fig = make_subplots(
            rows=5, cols=1, 
            shared_xaxes=True, # 共享X轴，拖动一个大家一起动
            vertical_spacing=0.05,
            subplot_titles=ROBOTS # 每一行上面显示机器名字
        )
        
        plot_df = df.tail(60) # 只看最近60秒
        colors = ['#00d4ff', '#00ff41', '#ffd700', '#ff00ff', '#e0e0e0']
        
        for i, robot in enumerate(ROBOTS):
            r_df = plot_df[plot_df['Robot_ID'] == robot]
            
            # 添加区域填充图 (Area Chart)
            fig.add_trace(go.Scatter(
                x=r_df['Timestamp'], y=r_df['Motor_Temperature'],
                mode='lines',
                fill='tozeroy', # 填充底部，视觉更稳
                line=dict(width=2, color=colors[i]),
                name=robot
            ), row=i+1, col=1)
            
            # 每一行的 Y轴 范围单独锁死！
            # 这样即使这台机器温度是40，那台是80，格子都不会乱跳
            fig.update_yaxes(range=[30, 100], showgrid=True, gridcolor='rgba(255,255,255,0.1)', row=i+1, col=1)
            
            # 预警线
            fig.add_hline(y=80, line_dash="dot", line_color="red", opacity=0.5, row=i+1, col=1)

        # === 核心防抖技术 ===
        fig.update_layout(
            height=600, # 固定高度
            margin=dict(l=60, r=20, t=40, b=40), # 【焊死边距】防止文字长短变化导致图表左右横跳
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False, # 既然分行了，就不需要图例了，清爽
            font=dict(color='#a0a0a0'),
            hovermode="x unified" # 鼠标放上去显示同一时刻所有机器数值
        )
        
        # 只在最后一行显示时间轴标签，上面几行隐藏
        fig.update_xaxes(showticklabels=False, showgrid=False)
        fig.update_xaxes(showticklabels=True, row=5, col=1)
        
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}") # Key 强制刷新

    # 4. 自动刷新
    time.sleep(refresh_rate)
    st.rerun()
