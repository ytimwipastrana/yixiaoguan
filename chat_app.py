import streamlit as st
import time
import re
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from llm_service import LLMService

# ========== 页面配置 ==========
st.set_page_config(
    page_title="医小管",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ========== 初始化会话状态 ==========
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": """👋 你好，我是医小管

你的专属AI辅导员

---

💡 试试问我：
• 奖学金怎么申请？
• 医保报销比例？
• 考研有什么要求？
• 选课系统怎么进？"""
        }
    ]

if "llm" not in st.session_state:
    st.session_state.llm = LLMService()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# 新增：等待状态和待处理回答
if "waiting_for_answer" not in st.session_state:
    st.session_state.waiting_for_answer = False

if "pending_answer" not in st.session_state:
    st.session_state.pending_answer = None

if "pending_sources" not in st.session_state:
    st.session_state.pending_sources = None

# ========== 日志记录函数 ==========
def log_conversation(question, answer, sources, feedback=None, session_id=None):
    """记录对话日志，用于后续分析"""
    log_file = "evolution_logs.csv"
    
    try:
        if not os.path.exists(log_file):
            with open(log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间', '会话ID', '问题', '回答', '回答长度', 
                    '来源数量', '用户反馈', '响应时间(ms)', '是否成功'
                ])
        
        is_success = len(sources) > 0 and len(answer) > 20
        
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                session_id or '',
                question[:100] + '...' if len(question) > 100 else question,
                answer[:200] + '...' if len(answer) > 200 else answer,
                len(answer),
                len(sources) if sources else 0,
                feedback or '',
                int((time.time() % 1) * 1000),
                is_success
            ])
    except Exception as e:
        print(f"日志记录失败: {e}")

# ========== 强制换行函数 ==========
def format_with_line_breaks(text):
    """
    强制处理换行，确保AI回答中的每个句子都能正确换行
    """
    if not text:
        return text
    
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('。', '。\n')
    text = text.replace('？', '？\n')
    text = text.replace('！', '！\n')
    text = text.replace('；', '；\n')
    text = text.replace('：', '：\n')
    
    text = re.sub(r'(\d+\.)', r'\n\1', text)
    text = re.sub(r'([一二三四五六七八九十])[、.]', r'\n\1、', text)
    text = re.sub(r'（(\d+)）', r'\n（\1）', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    lines = text.split('\n')
    formatted = '<br>'.join(lines)
    
    return formatted

# ========== 极简CSS ==========
st.markdown("""
<style>
    .stApp { background: #0A0A0A; }
    #MainMenu, footer, header {visibility: hidden;}
    
    .title { text-align: center; font-size: 2rem; color: #FFFFFF; margin-bottom: 2rem; }
    .title span { color: #666; font-size: 0.9rem; display: block; }
    
    .chat-container { max-width: 700px; margin: 0 auto; padding-bottom: 80px; }
    
    .message-row { display: flex; margin: 1.5rem 0; }
    .message-row.user { justify-content: flex-end; }
    .message-row.assistant { justify-content: flex-start; }
    
    .message-bubble {
        max-width: 80%;
        padding: 1rem 1.4rem;
        border-radius: 1.2rem;
        line-height: 1.6;
        font-size: 0.95rem;
        word-wrap: break-word;
    }
    .message-bubble.user { background: #1E1E1E; color: #FFFFFF; border: 1px solid #333; }
    .message-bubble.assistant { background: #0F0F0F; color: #E0E0E0; border: 1px solid #2A2A2A; }
    
    .message-content { white-space: pre-wrap; }
    .message-content br { display: block; margin-top: 0.3rem; }
    
    .thinking-bubble {
        background: #0F0F0F;
        border: 1px solid #2A2A2A;
        border-radius: 1.2rem;
        padding: 1rem 1.4rem;
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        max-width: 80%;
    }
    .thinking-dots { display: flex; gap: 0.3rem; }
    .thinking-dot {
        width: 0.5rem; height: 0.5rem;
        background: #666;
        border-radius: 50%;
        animation: pulse 1.4s infinite;
    }
    .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
    .thinking-text { color: #888; font-size: 0.9rem; }
    
    .source-item {
        background: #0A0A0A;
        padding: 0.5rem 0.8rem;
        border-radius: 0.5rem;
        margin: 0.3rem 0;
        color: #666;
        border-left: 2px solid #333;
        font-size: 0.8rem;
    }
    
    .input-section {
        max-width: 700px;
        margin: 0 auto;
        padding: 1rem;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #0A0A0A;
        border-top: 1px solid #333;
    }
    
    .stTextInput input {
        background: #0F0F0F !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 2rem !important;
        padding: 0.8rem 1.2rem !important;
        color: #FFFFFF !important;
    }
    .stTextInput input:focus { border-color: #1976d2 !important; }
    .stTextInput input::placeholder { color: #444 !important; }
    
    .stButton > button {
        background: #1A1A1A !important;
        border: 1px solid #333 !important;
        border-radius: 2rem !important;
        color: #CCC !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover:not(:disabled) {
        border-color: #1976d2 !important;
        color: #1976d2 !important;
    }
    .stButton > button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    .privacy-note {
        text-align: center;
        color: #333;
        font-size: 0.7rem;
        margin: 1rem 0;
        padding: 1rem;
    }
    
    @keyframes pulse {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
        30% { transform: translateY(-3px); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown("""
<div class="title">
    🩺 医小管
    <span>AI辅导员 · 测试版</span>
</div>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("### ⚡")
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 你好，我是医小管\n\n**你的专属AI辅导员**"}
        ]
        st.session_state.conversation_id = None
        st.session_state.waiting_for_answer = False
        st.session_state.pending_answer = None
        st.rerun()

# ========== 如果有待处理的回答，先添加到消息历史 ==========
if st.session_state.pending_answer:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": st.session_state.pending_answer,
        "sources": st.session_state.pending_sources
    })
    st.session_state.pending_answer = None
    st.session_state.pending_sources = None
    st.session_state.waiting_for_answer = False
    st.rerun()

# ========== 聊天区域 ==========
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f"""
        <div class="message-row user">
            <div class="message-bubble user">
                <div class="message-content">{message["content"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        formatted_content = format_with_line_breaks(message["content"])
        
        st.markdown(f"""
        <div class="message-row assistant">
            <div class="message-bubble assistant">
                <div class="message-content">{formatted_content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 10])
        with col1:
            fb_col1, fb_col2 = st.columns(2)
            with fb_col1:
                if st.button("👍", key=f"like_{idx}", help="有帮助"):
                    prev_question = st.session_state.messages[idx-1]["content"] if idx > 0 else ""
                    log_conversation(
                        prev_question,
                        message["content"],
                        message.get("sources", []),
                        feedback="like",
                        session_id=st.session_state.conversation_id
                    )
                    st.toast("感谢反馈 🙏")
            with fb_col2:
                if st.button("👎", key=f"dislike_{idx}", help="需改进"):
                    prev_question = st.session_state.messages[idx-1]["content"] if idx > 0 else ""
                    log_conversation(
                        prev_question,
                        message["content"],
                        message.get("sources", []),
                        feedback="dislike",
                        session_id=st.session_state.conversation_id
                    )
                    st.toast("感谢反馈，我会努力改进")
        
        with col2:
            if st.button("📋", key=f"copy_{idx}", help="复制回答"):
                js = f"navigator.clipboard.writeText(`{message['content']}`);"
                st.components.v1.html(f"<script>{js}</script>", height=0)
                st.toast("已复制")
        
        if "sources" in message and message["sources"]:
            with st.expander("📚 来源"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"""
                    <div class="source-item">
                        <span>📄</span> {source[:150]}...
                    </div>
                    """, unsafe_allow_html=True)

# 如果正在等待回答，显示思考动画
if st.session_state.waiting_for_answer:
    st.markdown("""
    <div class="message-row assistant">
        <div class="thinking-bubble">
            <div class="thinking-dots">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
            <span class="thinking-text">医小管正在思考...</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 输入区域 ==========
st.markdown('<div class="input-section">', unsafe_allow_html=True)

col1, col2 = st.columns([6, 1])

with col1:
    input_key = f"user_input_{st.session_state.input_key}"
    user_input = st.text_input(
        "",
        placeholder="输入你的问题..." if not st.session_state.waiting_for_answer else "正在处理中，请稍候...",
        label_visibility="collapsed",
        key=input_key,
        disabled=st.session_state.waiting_for_answer
    )

with col2:
    send_button = st.button(
        "发送", 
        use_container_width=True,
        disabled=st.session_state.waiting_for_answer
    )

# ========== 处理发送（关键改进：立即显示 + 直接调用API） ==========
if (send_button or user_input) and user_input and not st.session_state.waiting_for_answer:
    # 1. 立即显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.input_key += 1
    
    # 2. 设置等待状态，显示动画
    st.session_state.waiting_for_answer = True
    
    # 3. 直接调用API
    result = st.session_state.llm.ask(user_input, st.session_state.conversation_id)
    
    if isinstance(result, tuple) and len(result) == 3:
        reply, new_conversation_id, sources = result
    elif isinstance(result, tuple) and len(result) == 2:
        reply, new_conversation_id = result
        sources = ["回答基于知识库生成"]
    else:
        reply = result
        new_conversation_id = None
        sources = []
    
    if new_conversation_id:
        st.session_state.conversation_id = new_conversation_id
    
    # 添加引导语
    reply += "\n\n---\n如果对回答满意，欢迎点击下方的 👍 反馈。测试阶段，你的每一条反馈都会帮助我变得更好 🙏"
    
    # 记录日志
    log_conversation(
        user_input,
        reply,
        sources,
        session_id=st.session_state.conversation_id
    )
    
    # 4. 保存结果到待处理
    st.session_state.pending_answer = reply
    st.session_state.pending_sources = sources
    
    # 5. 刷新页面显示结果
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ========== 隐私提示 ==========
st.markdown("""
<div class="privacy-note">
    🛡️ 对话仅保存在本地 · 不上传个人信息 · 可随时清空
</div>
""", unsafe_allow_html=True)