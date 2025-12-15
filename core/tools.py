"""
核心工具集：邮件发送等通用动作
"""

import smtplib
import ssl
from email.mime.text import MIMEText

import streamlit as st


def send_email_action(content: str, subject: str = "自动警报", to_email: str | None = None) -> bool:
    """
    发送邮件（基于 secrets.toml 的 email 配置）

    Args:
        content: 邮件正文
        subject: 邮件标题
        to_email: 收件人，不传则默认发给配置里的发件人
    """
    try:
        email_conf = st.secrets["email"]
        smtp_server = email_conf["SMTP_SERVER"]
        smtp_port = int(email_conf.get("SMTP_PORT", 465))
        sender_email = email_conf["SENDER_EMAIL"]
        password = email_conf["EMAIL_PASSWORD"]
    except Exception as e:
        st.error(f"⚠️ 邮件配置缺失或错误: {e}")
        return False

    receiver = to_email or sender_email

    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, [receiver], msg.as_string())
        return True
    except Exception as e:
        st.error(f"❌ 邮件发送失败: {e}")
        return False

