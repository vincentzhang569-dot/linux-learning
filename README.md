# 🏭 工业机器人智能故障诊断系统

<div align="center">

**基于 Streamlit 和 LLM 的工业级故障诊断平台**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![在线体验](https://img.shields.io/badge/在线体验-Live-brightgreen.svg)](https://my-ai-brain-ngxgc6mxyspvxsj5adqdyw.streamlit.app/)

</div>

---

## 📋 简介

集成 AI 故障诊断、IoT 实时监控和智能控制的工业管理平台。支持多模态输入（图片、文档、文本），提供专业诊断建议和自然语言机器人控制。

## ✨ 核心功能

| 模块 | 功能 |
|------|------|
| **智能诊断** | 多模态故障分析、原理级诊断、结构化排查步骤 |
| **IoT 监控** | 实时数据可视化、趋势分析、异常预警 |
| **AI 控制** | 自然语言控制、批量操作、安全验证 |

## 🛠️ 技术栈

- **框架**: Streamlit 1.28+, Python 3.10+
- **AI**: SiliconFlow (Qwen2-VL-72B, Qwen2.5-Coder-32B)
- **数据处理**: Pandas, Plotly, PDFplumber

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/vincentzhang569-dot/my-ai-brain.git
cd my-ai-brain

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
# 创建 .streamlit/secrets.toml
echo 'SILICONFLOW_API_KEY = "your-api-key"' > .streamlit/secrets.toml

# 4. 运行应用
streamlit run main.py
```

> 💡 获取 API Key: [硅基流动](https://siliconflow.cn/)

## 📁 项目结构

```
my-ai-brain/
├── main.py              # 主入口
├── app.py               # 智能诊断
├── dashboard.py         # IoT 监控
├── commander.py         # AI 控制
├── core/                # 核心模块
│   └── llm_client.py    # LLM 客户端
└── requirements.txt     # 依赖
```

## 📄 许可证

[MIT License](LICENSE)

## 👤 作者

**vincentzhang569-dot**

- 📧 Email: vincentzhang569@gmail.com
- 🔗 GitHub: [@vincentzhang569-dot](https://github.com/vincentzhang569-dot)

---

<div align="center">

⭐ **如果这个项目对你有帮助，请给个 Star！**

</div>
