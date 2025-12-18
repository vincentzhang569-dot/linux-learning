import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from datetime import datetime, timedelta

# ==================== 1. 页面配置 (暗黑模式) ====================
st.set_page_config(
    page_title="工业监护中心",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 强制 CSS：纯黑背景，消除所有组件的内边距，防止布局跳动
st.markdown("""
<style>
    .main, .stApp { background-color: #000000; }
    
    /* 隐藏 Streamlit 默认头部和尾部 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 卡片样式 */
    .metric-card {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 10px;
        text-align: center;
    }
    
    /* 强制图表容器高度固定，这是防抖的关键 */
    iframe { height: 350px !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 2. 数据逻辑 ====================

ROBOTS = ['Robot_A01', 'Robot_B02', 'Robot_C03', 'Robot_D04', 'Robot_E05']

# 初始化 Session State
if 'data_buffer' not in st.session_state:
    now = datetime.now()
    init_data = []
    for robot in ROBOTS:
        # 初始值
        base_temp = np.random.uniform(45, 65)
        base_vib = np.random.uniform(0.3, 0.8)
        for i in range(60): # 初始化60秒数据
            ts = now - timedelta(seconds=(60-i))
            init_data.append({
                'Timestamp': ts, 'Robot_ID': robot,
                'Temp': base_temp, 'Vib': base_vib, 'Status': 'Running'
            })
    st.session_state.data_buffer = pd.DataFrame(init_data)

def simulate_data(df):
    """ 生成新数据 """
    last_time = df['Timestamp'].max()
    new_time = last_time + timedelta(seconds=1)
    new_rows = []
    
    # 获取最新状态
    latest = df.sort_values('Timestamp').groupby('Robot_ID').tail(1)
    
    for _, row in latest.iterrows():
        robot = row['Robot_ID']
        temp, vib = row['Temp'], row['Vib']
        
        # 模拟物理变化
        # 温度：随机游走
        temp += np.random.normal(0, 0.4)
        if temp > 85: temp -= 1.0 # 散热
        if temp < 40: temp += 0.5
        
        # 振动：偶尔波动
        if np.random.random() < 0.05: vib += np.random.choice([1.0, -0.5])
        vib = max(0.1, vib * 0.9 + np.random.normal(0.05, 0.01)) # 阻尼回落
        
        # 状态
        status = 'Running'
        if temp > 80 or vib > 5: status = 'Error'
        elif temp > 70 or vib > 3: status = 'Warning'
        
        new_rows.append({
            'Timestamp': new_time, 'Robot_ID': robot,
            'Temp': temp, 'Vib': vib, 'Status': status
        })
    return pd.DataFrame(new_rows)

# ==================== 3. 布局结构 (一次性建立，不再循环重建) ====================

st.markdown("## 📟 产线实时监控 (Real-time Monitor)")

# 占位符定义：先把坑挖好，后面只填坑，不挖坑
# 1. 顶部状态栏
status_placeholder = st.empty()

# 2. 图表区：拆分成左右两列！左边温度，右边振动！
col_temp, col_vib = st.columns(2)

with col_temp:
    st.markdown("### 🌡️ 电机温度 (°C)")
    temp_chart_placeholder = st.empty() # 温度图表的坑

with col_vib:
    st.markdown("### 📈 振动频率 (mm/s)")
    vib_chart_placeholder = st.empty() # 振动图表的坑

# ==================== 4. 绘图函数 (高度优化) ====================

def create_chart(df, data_col, color, y_range):
    """
    创建一个只包含线条的干净图表
    """
    # 使用 Subplots 也是为了对齐，5行1列
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=ROBOTS)
    
    for i, robot in enumerate(ROBOTS):
        r_data = df[df['Robot_ID'] == robot]
        
        fig.add_trace(go.Scatter(
            x=r_data['Timestamp'], y=r_data[data_col],
            mode='lines',
            line=dict(color=color, width=2),
            showlegend=False
        ), row=i+1, col=1)
        
        # 锁死坐标轴，防止跳动
        fig.update_yaxes(range=y_range, row=i+1, col=1, showgrid=True, gridcolor='#333', zeroline=False)
        
    # 全局布局优化
    fig.update_layout(
        height=350, # 高度写死
        margin=dict(l=10, r=10, t=20, b=10), # 边距写死
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        font=dict(color='#aaa', size=10),
        hovermode='x unified',
        xaxis5=dict(showticklabels=False) # 隐藏底部时间，保持极简
    )
    fig.update_xaxes(showgrid=False, visible=False) # 隐藏所有X轴线
    
    return fig

# ==================== 5. 主循环 (只更新数据) ====================

# 侧边栏控制
run = st.sidebar.checkbox('启动监控', value=True)

if run:
    while True:
        # A. 更新数据
        new_df = simulate_data(st.session_state.data_buffer)
        st.session_state.data_buffer = pd.concat([st.session_state.data_buffer, new_df], ignore_index=True).tail(60 * 5) # 保留足够数据
        df = st.session_state.data_buffer
        
        # B. 更新状态栏 (HTML 表格渲染，比 st.metric 更稳，不闪)
        latest = df.sort_values('Timestamp').groupby('Robot_ID').tail(1).reset_index()
        
        # 构造 HTML 字符串一次性渲染，而不是用 5 个 st.metric
        status_html = "<div style='display:flex; justify-content:space-between; margin-bottom:10px'>"
        for _, row in latest.iterrows():
            color = "#00BFFF" if row['Status']=='Running' else ("#FFD700" if row['Status']=='Warning' else "#FF0000")
            status_html += f"""
            <div style="background:#111; padding:10px; border-left:4px solid {color}; width:19%;">
                <div style="color:#fff; font-weight:bold;">{row['Robot_ID']}</div>
                <div style="color:{color}; font-size:12px;">{row['Status']}</div>
                <div style="color:#ccc; font-size:12px;">T:{row['Temp']:.1f} | V:{row['Vib']:.1f}</div>
            </div>
            """
        status_html += "</div>"
        status_placeholder.markdown(status_html, unsafe_allow_html=True)
        
        # C. 绘制并更新图表
        
        # 1. 温度图表 (蓝色)
        fig_temp = create_chart(df, 'Temp', '#00BFFF', [20, 100])
        # 【关键】使用 key 强制复用，但这里我们在循环外使用了 empty 容器
        # 只要容器不变，内容会被替换。为了防闪烁，我们不需要 key 了，直接覆盖。
        temp_chart_placeholder.plotly_chart(fig_temp, use_container_width=True, config={'staticPlot': True}) 
        # config={'staticPlot': True} 是大招！它禁止了图表的交互（缩放等），大大减少了重绘负担，彻底消除闪烁。
        
        # 2. 振动图表 (橙色/黄色，区分开)
        fig_vib = create_chart(df, 'Vib', '#FFA500', [0, 8])
        vib_chart_placeholder.plotly_chart(fig_vib, use_container_width=True, config={'staticPlot': True})
        
        # D. 等待
        time.sleep(1) # 1秒刷新一次
