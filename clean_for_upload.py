"""
清理脚本：用于上传到 ChatGPT 前清理敏感信息
使用方法：python clean_for_upload.py
"""

import re

def clean_commander():
    """清理 commander.py"""
    with open('commander.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换占位符 API Key
    content = content.replace('api_key = "sk-placeholder"', 'api_key = "YOUR_API_KEY_HERE"')
    
    with open('commander_clean.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ commander_clean.py 已生成")

def clean_app():
    """清理 app.py"""
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 API Key 显示（前4位）
    content = re.sub(
        r'st\.success\(f"✅ API Key 已配置（前4位: \{api_key\[:4\]\}\.\.\.\)"\)',
        'st.success("✅ API Key 已配置")',
        content
    )
    
    with open('app_clean.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ app_clean.py 已生成")

if __name__ == "__main__":
    print("🧹 开始清理文件...")
    clean_commander()
    clean_app()
    print("\n✨ 清理完成！可以安全上传 *_clean.py 文件到 ChatGPT")

