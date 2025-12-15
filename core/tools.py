import smtplib
import json
import streamlit as st
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr  # <--- 引入这个标准工具

# === 1. 定义工具函数 ===
def send_email_action(to_email: str, subject: str, content: str):
    """
    发送邮件的实际执行函数 (QQ邮箱 RFC标准版)
    """
    try:
        # 获取配置
        email_config = st.secrets["email"]
        smtp_server = email_config["SMTP_SERVER"]
        smtp_port = email_config["SMTP_PORT"]
        sender = email_config["SENDER_EMAIL"]
        password = email_config["EMAIL_PASSWORD"]

        # 构造邮件
        message = MIMEText(content, 'plain', 'utf-8')
        
        # === 核心修复：使用 formataddr 生成符合 RFC 标准的头部 ===
        # 这样生成的格式是： =?utf-8?b?xxx?= <sender@qq.com>
        # QQ 邮箱绝对挑不出毛病
        message['From'] = formataddr(("工业智脑中控", sender))
        message['To'] = formataddr(("管理员", to_email))
        message['Subject'] = Header(subject, 'utf-8')

        # 发送
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        server.sendmail(sender, [to_email], message.as_string())
        
        # 优雅退出
        try:
            server.quit()
        except Exception:
            pass
        
        return json.dumps({"status": "success", "msg": f"已成功发送邮件至 {to_email}"})
        
    except Exception as e:
        # 打印错误到终端方便调试，同时返回给前端
        print(f"Email Error: {e}")
        return json.dumps({"status": "error", "msg": f"邮件发送失败: {str(e)}"})

# === 2. 定义给 GLM-4 看的说明书 (JSON Schema) ===
GLM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email_action",
            "description": "当检测到设备故障、温度过高或需要通知管理人员时，调用此函数发送报警邮件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "接收人的邮箱地址"
                    },
                    "subject": {
                        "type": "string",
                        "description": "邮件标题，应包含【警报】字样"
                    },
                    "content": {
                        "type": "string",
                        "description": "邮件正文，包含具体的故障信息、温度数值或建议"
                    }
                },
                "required": ["to_email", "subject", "content"]
            }
        }
    }
]