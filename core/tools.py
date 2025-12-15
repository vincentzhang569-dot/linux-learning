"""
核心工具集：邮件发送等通用动作
"""

import json
import smtplib
from email.header import Header
from email.mime.text import MIMEText

import streamlit as st


def send_email_action(to_email: str, subject: str, content: str):
    """
    发送邮件的实际执行函数 (QQ邮箱修正版)
    """
    try:
        # 获取配置
        email_config = st.secrets["email"]
        smtp_server = email_config["SMTP_SERVER"]
        smtp_port = email_config["SMTP_PORT"]
        sender = email_config["SENDER_EMAIL"]
        password = email_config["EMAIL_PASSWORD"]

        # 构造邮件
        message = MIMEText(content, "plain", "utf-8")

        # === 关键修改 ===
        # 格式：工业智脑中控 <970859897@qq.com>
        # 这样 QQ 才会认为你是合法用户
        message["From"] = f"工业智脑中控 <{sender}>"
        # =================

        message["To"] = f"<{to_email}>"
        message["Subject"] = Header(subject, "utf-8")

        # 发送
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        server.sendmail(sender, [to_email], message.as_string())

        try:
            server.quit()
        except Exception:
            pass

        return json.dumps({"status": "success", "msg": f"已成功发送邮件至 {to_email}"})

    except Exception as e:
        return json.dumps({"status": "error", "msg": f"邮件发送失败: {str(e)}"})

