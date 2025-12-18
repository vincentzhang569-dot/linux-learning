import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 1. 页面与CSS配置 ====================
st.set_page_config(
    page_title="工业监护中心",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS: 纯黑背景 + 蓝色系微调
st.markdown("""
<style>
    .main, .stApp { background-color: #000000; }
    
    /* 卡片样式 */
    .metric-card {
        background-color: #111;
        border: 1px solid #333;
        border-left: 5px solid #555;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 10px;
    }
    /* 状态指示灯颜色 */
    .status-running { border-left-color: #00BFFF; box-shadow: -2px 0 10px rgba(0,191,255,0.1); } /* 正常改成蓝色 */
    .status-warning { border-left-color: #ffcc00; box-shadow: -2px 0 10px rgba(255,204,0,0.1); }
    .status-error   { border-left-color: #ff0000; box-shadow: -2px 0 10px rgba(255,0,0,0.2); }
    
    .robot-title { color: #fff; font-family: monospace; font-size: 16px; font-weight: bold; }
    .metric-val { color: #aaa; font-family: monospace; font-size: 14px; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .js-plotly-plot { height: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 2. 数据引擎 ====================

ROBOTS = ['Robot_A01', 'Robot_B02', 'Robot_C03', 'Robot_D04', 'Robot_E05']

if 'data_buffer' not in st.session_state:
    now = datetime.now()
    init_data = []
    for r_idx, robot in enumerate(ROBOTS):
        base_temp = 50 + (r_idx * 5)
        base_vib = 0.5 + (r_idx * 0.2)
        for i in range(100):
            ts = now - timedelta(seconds=(100-i))
            init_data.append({
                'Timestamp': ts, 'Robot_ID': robot,
                'Temp': base_temp + np.random.normal(0, 0.5),
                'Vib': base_vib + np.random.normal(0, 0.1),
                'Status': 'Running'
            })
    st.session_state.data_buffer = pd.DataFrame(init_data)

def simulate_stream(df):
    last_time = df['Timestamp'].max()
    new_time = last_time + timedelta(seconds=1)
    new_rows = []
    
    last_state = df.sort_values('Timestamp').groupby('Robot_ID').tail(1)
    
    for _, row in last_state.iterrows():
        robot = row['Robot_ID']
        prev_temp = row['Temp']
        prev_vib = row['Vib']
        
        # 模拟逻辑
        delta_t = np.random.normal(0, 0.6) 
        if prev_temp > 85: delta_t = -1.5 
        new_temp = prev_temp + delta_t
        
        if np.random.random() < 0.05: 
            new_vib = prev_vib + np.random.choice([1.5, -1.0])
        else:
            new_vib = prev_vib + np.random.normal(0, 0.1)
        new_vib = max(0.1, new_vib * 0.95)
        
        status = 'Running'
        if new_temp > 85 or new_vib > 6: status = 'Error'
        elif new_temp > 75 or new_vib > 4: status = 'Warning'
        
        new_rows.append({
            'Timestamp': new_time, 'Robot_ID': robot,
            'Temp': new_temp, 'Vib': new_vib, 'Status': status
        })
    
    return pd.DataFrame(new_rows)

# ==================== 3. 布局 ====================

c1, c2 = st.columns([4, 1])
c1.markdown("## 📟 产线设备信号监控 (Live Signal)")
time_placeholder = c2.empty()
metrics_placeholder = st.empty()
chart_placeholder = st.empty()

with st.sidebar:
    run = st.toggle('启动实时监控', value=True)
    refresh_rate = st.slider('刷新间隔 (秒)', 0.1, 2.0, 1.0)

# ==================== 4. 循环逻辑 ====================

if run:
    while True:
        # A. 数据更新
        new_frame = simulate_stream(st.session_state.data_buffer)
        st.session_state.data_buffer = pd.concat(
            [st.session_state.data_buffer, new_frame], ignore_index=True
        ).tail(300) 
        df = st.session_state.data_buffer
        
        # B. 渲染时间
        time_placeholder.markdown(
            f"<div style='text-align:right; font-family:monospace; color:#00BFFF; font-size:20px'>{datetime.now().strftime('%H:%M:%S')}</div>", 
            unsafe_allow_html=True
        )
        
        # C. 渲染卡片
        latest = df.sort_values('Timestamp').groupby('Robot_ID').tail(1).reset_index()
        with metrics_placeholder.container():
            cols = st.columns(5)
            for i, row in latest.iterrows():
                stt = row['Status']
                css_cls = f"status-{stt.lower()}"
                # 状态图标颜色
                icon = "🔵" if stt=='Running' else "🟡" if stt=='Warning' else "🔴"
                cols[i].markdown(f"""
                <div class="metric-card {css_cls}">
                    <div class="robot-title">{row['Robot_ID']}</div>
                    <div style="font-size:12px; color:#666;">{icon} {stt}</div>
                    <div class="metric-val">T: {row['Temp']:.1f}°C</div>
                    <div class="metric-val">V: {row['Vib']:.2f} G</div>
                </div>
                """, unsafe_allow_html=True)

        # D. 渲染图表
        fig = make_subplots(
            rows=5, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03, 
            subplot_titles=None 
        )

        for i, robot in enumerate(ROBOTS):
            r_data = df[df['Robot_ID'] == robot]
            
            # === 修改颜色为科技蓝 (#00BFFF) ===
            fig.add_trace(go.Scatter(
                x=r_data['Timestamp'], 
                y=r_data['Temp'], 
                mode='lines',
                line=dict(color='#00BFFF', width=2), # 这里改成了蓝色
                name=robot,
                showlegend=False
            ), row=i+1, col=1)
            
            target_xref = "x domain" if i == 0 else f"x{i+1} domain"
            target_yref = "y domain" if i == 0 else f"y{i+1} domain"

            # 标签
            fig.add_annotation(
                text=f"<b>{robot}</b>",
                xref=target_xref, yref=target_yref,
                x=0.01, y=0.85, showarrow=False,
                font=dict(color="white", size=10),
                bgcolor="rgba(0,0,0,0.5)" # 加个半透明背景防遮挡
            )

            # 坐标轴样式
            fig.update_yaxes(
                range=[20, 100], 
                row=i+1, col=1,
                showgrid=True, gridcolor='#333', gridwidth=1,
                zeroline=False,
                tickfont=dict(size=8, color='#666')
            )

        fig.update_layout(
            height=600, 
            margin=dict(l=10, r=10, t=20, b=20),
            paper_bgcolor='#000000', 
            plot_bgcolor='#000000',  
            xaxis=dict(showgrid=False, visible=False), 
            xaxis5=dict(showgrid=True, gridcolor='#333', tickfont=dict(color='#666')), 
            hovermode='x unified'
        )

        # === 修复点：移除了 key="monitor_chart" ===
        # 因为我们是在 while 循环里调用，chart_placeholder 已经锁定了位置
        # 直接由占位符负责更新，不需要 Key，这样就不会报错了
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        
        time.sleep(refresh_rate)
