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
    发送邮件的实际执行函数 (抗干扰版)
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
        message["From"] = Header("工业智脑中控 <AI_Center>", "utf-8")
        message["To"] = Header(to_email, "utf-8")
        message["Subject"] = Header(subject, "utf-8")

        # 发送
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        server.sendmail(sender, [to_email], message.as_string())

        # === 关键修复：优雅退出 ===
        try:
            server.quit()
        except Exception:
            # 如果邮件已发送但断开连接报错，忽略它，视为成功
            pass

        return json.dumps({"status": "success", "msg": f"已成功发送邮件至 {to_email}"})

    except Exception as e:
        return json.dumps({"status": "error", "msg": f"邮件发送失败: {str(e)}"})

