import streamlit as st
import time
import re
import csv
import os
from datetime import datetime
from llm_service import LLMService

# ========== 页面配置 ==========
st.set_page_config(
    page_title="医小管",
    page_icon="🩺",
    layout="centered"
)

# ========== 初始化 ==========
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 你好，我是医小管\n\n你的专属AI辅导员"}
    ]

if "llm" not in st.session_state:
    st.session_state.llm = LLMService()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# ========== 日志记录 ==========
def log_conversation(question, answer, feedback=None):
    log_file = "evolution_logs.csv"
    try:
        if not os.path.exists(log_file):
            with open(log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['时间', '问题', '回答', '反馈'])
        
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                question[:100],
                answer[:100],
                feedback or ''
            ])
    except:
        pass

# ========== 显示消息 ==========
st.title("🩺 医小管")

# 显示所有历史消息
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # 如果是AI消息，添加反馈按钮
        if msg["role"] == "assistant" and idx > 0:
            col1, col2, col3 = st.columns([1, 1, 8])
            with col1:
                if st.button("👍", key=f"like_{idx}"):
                    prev_q = st.session_state.messages[idx-1]["content"]
                    log_conversation(prev_q, msg["content"], "like")
                    st.toast("感谢反馈 🙏")
            with col2:
                if st.button("👎", key=f"dislike_{idx}"):
                    prev_q = st.session_state.messages[idx-1]["content"]
                    log_conversation(prev_q, msg["content"], "dislike")
                    st.toast("感谢反馈 🙏")
            with col3:
                if st.button("📋", key=f"copy_{idx}"):
                    st.toast("已复制")

# ========== 输入 ==========
prompt = st.chat_input("输入你的问题...")

# ========== 处理 ==========
if prompt:
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 获取AI回答
    with st.chat_message("assistant"):
        with st.spinner("医小管正在思考..."):
            result = st.session_state.llm.ask(prompt, st.session_state.conversation_id)
            
            if isinstance(result, tuple) and len(result) >= 2:
                reply = result[0]
                if len(result) >= 2:
                    st.session_state.conversation_id = result[1]
            else:
                reply = str(result)
            
            # 添加引导语
            reply += "\n\n---\n如果对回答满意，欢迎点击下方的 👍 反馈。"
            
            st.markdown(reply)
    
    # 保存回答
    st.session_state.messages.append({"role": "assistant", "content": reply})
    log_conversation(prompt, reply)
    
    st.rerun()