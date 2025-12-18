import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 1. 页面配置 ====================
st.set_page_config(
    page_title="工业监护中心",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS: 强制黑底，修复卡片样式，去掉白色方框背景
st.markdown("""
<style>
    .main, .stApp { background-color: #000000; }
    
    /* 隐藏 Streamlit 默认头部 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 顶部卡片容器样式 */
    .card-container {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    /* 单个卡片样式 */
    .robot-card {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 5px;
        padding: 10px;
        width: 19%; /* 5个卡片平分 */
        text-align: center;
        box-shadow: 0 0 5px rgba(0,0,0,0.5);
    }
    
    /* 状态颜色边框 */
    .status-normal { border-top: 3px solid #00BFFF; } /* 正常蓝 */
    .status-warning { border-top: 3px solid #FFA500; } /* 警告橙 */
    .status-error { border-top: 3px solid #FF0000; }   /* 错误红 */
    
    /* 字体样式 */
    .card-title { color: #fff; font-weight: bold; font-size: 16px; margin-bottom: 5px; }
    .card-status { font-size: 12px; margin-bottom: 5px; }
    .card-data { color: #ccc; font-family: monospace; font-size: 13px; }
    
    /* 强制图表高度 */
    .js-plotly-plot { height: 400px !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 2. 数据逻辑 ====================

ROBOTS = ['Robot_A01', 'Robot_B02', 'Robot_C03', 'Robot_D04', 'Robot_E05']

if 'data_buffer' not in st.session_state:
    now = datetime.now()
    init_data = []
    for robot in ROBOTS:
        base_temp = np.random.uniform(50, 60)
        base_vib = np.random.uniform(0.3, 0.6)
        for i in range(50):
            ts = now - timedelta(seconds=(50-i))
            init_data.append({
                'Timestamp': ts, 'Robot_ID': robot,
                'Temp': base_temp, 'Vib': base_vib, 'Status': 'Running'
            })
    st.session_state.data_buffer = pd.DataFrame(init_data)

def simulate_data(df):
    last_time = df['Timestamp'].max()
    new_time = last_time + timedelta(seconds=1)
    new_rows = []
    
    latest = df.sort_values('Timestamp').groupby('Robot_ID').tail(1)
    
    for _, row in latest.iterrows():
        robot = row['Robot_ID']
        temp, vib = row['Temp'], row['Vib']
        
        # 模拟数据波动
        temp += np.random.normal(0, 0.3)
        if temp > 80: temp -= 0.5
        if temp < 45: temp += 0.5
        
        if np.random.random() < 0.1: vib += np.random.choice([0.8, -0.4])
        vib = max(0.1, vib * 0.92 + np.random.normal(0.05, 0.01))
        
        status = 'Running'
        if temp > 75 or vib > 5: status = 'Error'
        elif temp > 65 or vib > 3: status = 'Warning'
        
        new_rows.append({
            'Timestamp': new_time, 'Robot_ID': robot,
            'Temp': temp, 'Vib': vib, 'Status': status
        })
    return pd.DataFrame(new_rows)

# ==================== 3. 布局结构 ====================

st.markdown("### 🏭 产线核心设备温控中心 (Live Monitor)")

# 1. 顶部：5个机器人卡片占位符
top_cards_placeholder = st.empty()

# 2. 下部：左右分栏图表
# 左边看温度，右边看振动，互不干扰，清晰明了
c1, c2 = st.columns(2)
with c1:
    st.markdown("**🔵 电机温度监控 (°C)**")
    temp_chart_placeholder = st.empty()
with c2:
    st.markdown("**🟠 振动频率监控 (mm/s)**")
    vib_chart_placeholder = st.empty()

# ==================== 4. 绘图函数 ====================

def create_subplot_chart(df, y_col, color, y_range):
    # 5行1列的图表，不显示图例，极简模式
    fig = make_subplots(
        rows=5, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        subplot_titles=None # 去掉标题，为了节省空间，直接写在图里
    )
    
    for i, robot in enumerate(ROBOTS):
        r_data = df[df['Robot_ID'] == robot]
        
        fig.add_trace(go.Scatter(
            x=r_data['Timestamp'], y=r_data[y_col],
            mode='lines',
            line=dict(color=color, width=2),
            showlegend=False
        ), row=i+1, col=1)
        
        # 在图表左上角内嵌文字，标明是哪个机器人，比外部标题更省空间且不乱
        fig.add_annotation(
            text=f"<b>{robot}</b>",
            xref=f"x domain", yref=f"y domain" if i==0 else f"y{i+1} domain",
            x=0.01, y=0.8, showarrow=False,
            font=dict(color="white", size=10),
            bgcolor="rgba(0,0,0,0.5)"
        )

        fig.update_yaxes(
            range=y_range, 
            row=i+1, col=1, 
            showgrid=True, gridcolor='#333', 
            zeroline=False,
            tickfont=dict(size=8, color='#888')
        )
        
    fig.update_layout(
        height=500, # 高度适中
        margin=dict(l=0, r=0, t=10, b=10),
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        hovermode='x unified',
        xaxis5=dict(showticklabels=False, showgrid=False) # 隐藏底部X轴
    )
    fig.update_xaxes(showgrid=False, visible=False)
    
    return fig

# ==================== 5. 运行循环 ====================

while True:
    # --- 数据更新 ---
    new_frame = simulate_data(st.session_state.data_buffer)
    st.session_state.data_buffer = pd.concat([st.session_state.data_buffer, new_frame], ignore_index=True).tail(100)
    df = st.session_state.data_buffer
    latest = df.sort_values('Timestamp').groupby('Robot_ID').tail(1)
    
    # --- 渲染顶部 5 个卡片 (HTML构建) ---
    # 这一步构建 HTML 字符串，不再会有缩进问题
    cards_html = '<div class="card-container">'
    for _, row in latest.iterrows():
        status = row['Status']
        
        # 样式判定
        if status == 'Running':
            css_class = 'status-normal'
            status_color = '#00BFFF'
            icon = '🟢'
        elif status == 'Warning':
            css_class = 'status-warning'
            status_color = '#FFA500'
            icon = '🟡'
        else:
            css_class = 'status-error'
            status_color = '#FF0000'
            icon = '🔴'
            
        cards_html += f"""
        <div class="robot-card {css_class}">
            <div class="card-title">{row['Robot_ID']}</div>
            <div class="card-status" style="color:{status_color}">{icon} {status}</div>
            <div class="card-data">T: {row['Temp']:.1f}°C</div>
            <div class="card-data">V: {row['Vib']:.2f}</div>
        </div>
        """
    cards_html += '</div>'
    
    # 渲染卡片
    top_cards_placeholder.markdown(cards_html, unsafe_allow_html=True)
    
    # --- 渲染图表 ---
    
    # 左侧：温度 (蓝色)
    fig_temp = create_subplot_chart(df, 'Temp', '#00BFFF', [40, 90])
    # 关键：staticPlot=True 彻底禁止交互层，解决手机端闪烁
    temp_chart_placeholder.plotly_chart(fig_temp, use_container_width=True, config={'staticPlot': True})
    
    # 右侧：振动 (橙色)
    fig_vib = create_subplot_chart(df, 'Vib', '#FFA500', [0, 8])
    vib_chart_placeholder.plotly_chart(fig_vib, use_container_width=True, config={'staticPlot': True})
    
    time.sleep(1.0)
