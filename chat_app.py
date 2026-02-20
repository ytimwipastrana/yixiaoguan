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

# ========== 极简初始化 ==========
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 你好，我是医小管\n\n你的专属AI辅导员"}
    ]

if "llm" not in st.session_state:
    st.session_state.llm = LLMService()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# ========== 最简聊天界面 ==========
st.title("🩺 医小管")

# 显示消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框（用最简单的形式）
prompt = st.chat_input("输入你的问题...")

# ========== 最简处理逻辑 ==========
if prompt:
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示思考动画
    with st.chat_message("assistant"):
        with st.spinner("医小管正在思考..."):
            # 调用API
            result = st.session_state.llm.ask(prompt, st.session_state.conversation_id)
            
            # 解析结果
            if isinstance(result, tuple) and len(result) >= 2:
                reply = result[0]
                if len(result) >= 2:
                    st.session_state.conversation_id = result[1]
            else:
                reply = str(result)
            
            # 显示回答
            st.markdown(reply)
    
    # 保存回答
    st.session_state.messages.append({"role": "assistant", "content": reply})
    
    # 强制刷新（确保显示）
    st.rerun()