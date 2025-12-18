import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 1. 基础配置 ====================
st.set_page_config(
    page_title="工业监护中心",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 强制 CSS：黑底，修复卡片样式
st.markdown("""
<style>
    .main, .stApp { background-color: #000000; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 顶部容器布局 */
    .css-18e3th9 { padding-top: 0rem; }
    
    /* 强制图表容器高度固定，防止页面抖动 */
    .js-plotly-plot { height: 450px !important; }
    
    /* 消除图表周围的留白 */
    .plotly .modebar { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 2. 数据引擎 ====================
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
        
        # 模拟波动
        temp += np.random.normal(0, 0.3)
        if temp > 80: temp -= 0.5
        if temp < 45: temp += 0.5
        
        if np.random.random() < 0.1: vib += np.random.choice([0.5, -0.3])
        vib = max(0.1, vib * 0.95 + np.random.normal(0.05, 0.01))
        
        status = 'Running'
        if temp > 75 or vib > 5: status = 'Error'
        elif temp > 65 or vib > 3: status = 'Warning'
        
        new_rows.append({
            'Timestamp': new_time, 'Robot_ID': robot,
            'Temp': temp, 'Vib': vib, 'Status': status
        })
    return pd.DataFrame(new_rows)

# ==================== 3. 布局占位符 (一次性建立) ====================

st.markdown("### 🏭 产线设备实时监控中心")

# 顶部卡片区域
cards_placeholder = st.empty()

# 图表区域 (左右分栏)
c1, c2 = st.columns(2)
with c1:
    st.markdown("**🔵 电机温度 (Temperature)**")
    chart_temp_place = st.empty()
with c2:
    st.markdown("**🟠 振动频率 (Vibration)**")
    chart_vib_place = st.empty()

# ==================== 4. 绘图函数 ====================
def create_chart(df, data_col, color_hex, y_range):
    # 创建 5 行 1 列的子图
    fig = make_subplots(
        rows=5, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.03, # 增加一点间距
        subplot_titles=None
    )
    
    for i, robot in enumerate(ROBOTS):
        r_data = df[df['Robot_ID'] == robot]
        
        # 线条：只画这一条！不再加任何警戒线！
        fig.add_trace(go.Scatter(
            x=r_data['Timestamp'], 
            y=r_data[data_col],
            mode='lines',
            line=dict(color=color_hex, width=2),
            showlegend=False
        ), row=i+1, col=1)
        
        # 标签 (内嵌在图表左侧，避免被遮挡)
        fig.add_annotation(
            text=f"<b>{robot}</b>",
            xref="paper", yref="paper",
            x=0.01, y=0.8,
            showarrow=False,
            font=dict(color="white", size=12),
            bgcolor="rgba(0,0,0,0.5)"
        )
        
        # Y轴固定，去掉网格线，只留纯净的数据
        fig.update_yaxes(
            range=y_range, 
            row=i+1, col=1, 
            showgrid=False, # 关掉网格，解决"四条线"视觉干扰
            zeroline=False,
            tickfont=dict(color='#666', size=10)
        )

    # 全局布局
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=10, b=10),
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        xaxis5=dict(showticklabels=False, showgrid=False), # 隐藏底部时间轴
        hovermode=False # 关闭悬停交互以提升极速性能
    )
    fig.update_xaxes(visible=False, showgrid=False)
    
    return fig

# ==================== 5. 主循环 ====================

# 预先定义 HTML 模板，这次压缩成单行，绝对不会显示出白色代码框
card_style = """<style>.monitor-container{display:flex;gap:8px;width:100%;}.monitor-card{background:#111;border:1px solid #333;border-radius:4px;flex:1;padding:10px;text-align:center;}.st-run{border-top:3px solid #00BFFF;}.st-warn{border-top:3px solid #FFA500;}.st-err{border-top:3px solid #FF0000;}.m-title{color:#fff;font-weight:bold;font-size:14px;margin-bottom:4px;}.m-val{color:#aaa;font-family:monospace;font-size:12px;}</style>"""

while True:
    # 1. 更新数据
    new_frame = simulate_data(st.session_state.data_buffer)
    st.session_state.data_buffer = pd.concat([st.session_state.data_buffer, new_frame], ignore_index=True).tail(50) # 只保留最近50个点，让线条跑得快一点
    df = st.session_state.data_buffer
    
    # 2. 生成顶部卡片 HTML (单行压缩，避免缩进错误)
    latest = df.sort_values('Timestamp').groupby('Robot_ID').tail(1)
    
    html_content = '<div class="monitor-container">'
    for _, row in latest.iterrows():
        status_cls = "st-run" if row['Status']=='Running' else ("st-warn" if row['Status']=='Warning' else "st-err")
        icon = "🟢" if row['Status']=='Running' else ("🟡" if row['Status']=='Warning' else "🔴")
        
        # 这是一个整块的 HTML 字符串，没有换行符干扰
        html_content += f"""<div class="monitor-card {status_cls}"><div class="m-title">{row['Robot_ID']}</div><div style="font-size:12px;color:#eee">{icon} {row['Status']}</div><div class="m-val">T:{row['Temp']:.1f} | V:{row['Vib']:.2f}</div></div>"""
        
    html_content += '</div>'
    
    # 渲染卡片 (unsafe_allow_html 必须开启)
    cards_placeholder.markdown(card_style + html_content, unsafe_allow_html=True)
    
    # 3. 渲染两个图表
    # 左边温度
    fig_t = create_chart(df, 'Temp', '#00BFFF', [40, 90])
    chart_temp_place.plotly_chart(fig_t, use_container_width=True, config={'staticPlot': True})
    
    # 右边振动
    fig_v = create_chart(df, 'Vib', '#FFA500', [0, 8])
    chart_vib_place.plotly_chart(fig_v, use_container_width=True, config={'staticPlot': True})
    
    time.sleep(1)
