import streamlit as st

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="工业智脑综合管理平台",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. 暴力 CSS 修复 (针对 Streamlit 内部结构) ---
st.markdown("""
    <style>
        /* === 1. 侧边栏整体背景变深，突出前景 === */
        [data-testid="stSidebar"] {
            background-color: #0E1117 !important; /* 极深色背景 */
            border-right: 1px solid #333;
        }

        /* === 2. 导航区域容器调整 === */
        div[data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }

        /* === 3. 核心修复：针对每一个导航链接 (a标签) === */
        div[data-testid="stSidebarNav"] li a {
            background-color: #262730 !important; /* 未选中时的背景：深灰色卡片 */
            border: 1px solid #464B5C !important; /* 明显的边框 */
            border-radius: 8px !important;
            padding: 12px 15px !important;
            margin-bottom: 10px !important;
            transition: all 0.2s;
        }

        /* === 4. 核弹级文字修复：强制内部所有元素变白 === */
        /* 不管是图标(svg)还是文字(span)，统统变白 */
        div[data-testid="stSidebarNav"] li a * {
            color: #FFFFFF !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            fill: #FFFFFF !important; /* SVG图标变白 */
        }

        /* === 5. 选中状态：高亮蓝 === */
        div[data-testid="stSidebarNav"] li a[aria-current="page"] {
            background-color: #667eea !important; /* 品牌蓝背景 */
            border-color: #667eea !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        /* 选中状态下的文字和图标也强制变白 */
        div[data-testid="stSidebarNav"] li a[aria-current="page"] * {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
        }

        /* === 6. 鼠标悬停状态 === */
        div[data-testid="stSidebarNav"] li a:hover {
            border-color: #FFFFFF !important; /* 悬停时边框变白 */
            background-color: #363B47 !important;
            transform: translateX(5px); /* 微微右移 */
        }

        /* === 7. 手机端左上角箭头修复 === */
        header {
            background: transparent !important;
            visibility: visible !important;
        }
        /* 强制汉堡菜单/箭头变白 */
        header button[kind="header"] {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
        }
        /* 隐藏多余元素 */
        header .stAppDeployButton, header .decoration {display: none;}
        footer {visibility: hidden;}
        
        /* 移动端顶部留白 */
        .block-container {padding-top: 3rem !important;}
        
        /* 侧边栏 Logo 文字修复 */
        .sidebar-text-container {
            color: #FFFFFF !important;
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. 定义页面路由 ---
pg = st.navigation([
    st.Page("app.py", title="智能故障诊断", icon="🚑", default=True),
    st.Page("dashboard.py", title="IoT 监控大屏", icon="📊"),
    st.Page("commander.py", title="AI 指挥官 (Agent)", icon="🎮"),
])

# --- 4. 侧边栏头部 (Logo区) ---
with st.sidebar:
    # 使用自定义 HTML 确保样式不被覆盖
    st.markdown("""
        <div class="sidebar-text-container">
            <div style="font-size: 42px; margin-bottom: 5px;">🏭</div>
            <div style="font-size: 20px; font-weight: 900; color: #FFF; letter-spacing: 1px;">工业 4.0 中台</div>
            <div style="font-size: 12px; color: #AAA; margin-top: 5px;">INDUSTRIAL AI BRAIN v2.0</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. 启动导航 ---
pg.run()





