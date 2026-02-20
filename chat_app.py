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

# 新增：控制动画显示的状态
if "show_thinking" not in st.session_state:
    st.session_state.show_thinking = False
    
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

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
    
    # 1. 处理各种换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2. 在中文标点符号后添加换行
    text = text.replace('。', '。\n')
    text = text.replace('？', '？\n')
    text = text.replace('！', '！\n')
    text = text.replace('；', '；\n')
    text = text.replace('：', '：\n')
    
    # 3. 在数字序号前添加换行（如 1. 2. 3. 或 一、二、三）
    text = re.sub(r'(\d+\.)', r'\n\1', text)
    text = re.sub(r'([一二三四五六七八九十])[、.]', r'\n\1、', text)
    
    # 4. 处理括号内的序号
    text = re.sub(r'（(\d+)）', r'\n（\1）', text)
    
    # 5. 将连续的换行符替换为单个换行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 6. 最后将换行符转换为HTML的<br>标签
    lines = text.split('\n')
    formatted = '<br>'.join(lines)
    
    return formatted

# ========== 极简CSS（高级感） ==========
st.markdown("""
<style>
    /* 全局样式 - 极简高级 */
    .stApp {
        background: #0A0A0A;
    }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 标题 - 极简 */
    .title {
        text-align: center;
        font-size: 2rem;
        font-weight: 400;
        color: #FFFFFF;
        margin-bottom: 2rem;
        letter-spacing: 1px;
    }
    
    .title span {
        color: #666;
        font-size: 0.9rem;
        display: block;
        font-weight: 300;
    }
    
    /* 聊天容器 */
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
    }
    
    /* 消息行 */
    .message-row {
        display: flex;
        margin: 1.5rem 0;
        animation: fadeIn 0.3s ease;
    }
    
    .message-row.user {
        justify-content: flex-end;
    }
    
    .message-row.assistant {
        justify-content: flex-start;
    }
    
    /* 消息气泡 - 极简设计 */
    .message-bubble {
        max-width: 80%;
        padding: 1rem 1.4rem;
        border-radius: 1.2rem;
        line-height: 1.6;
        font-size: 0.95rem;
        word-wrap: break-word;
    }
    
    .message-bubble.user {
        background: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #333;
    }
    
    .message-bubble.assistant {
        background: #0F0F0F;
        color: #E0E0E0;
        border: 1px solid #2A2A2A;
    }
    
    /* 消息内容 - 强制换行 */
    .message-content {
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .message-content br {
        display: block;
        content: "";
        margin-top: 0.3rem;
    }
    
    /* 思考动画样式 */
    .thinking-container {
        display: flex;
        justify-content: flex-start;
        margin: 1.5rem 0;
        animation: fadeIn 0.3s ease;
    }
    
    .thinking-bubble {
        background: #0F0F0F;
        border: 1px solid #2A2A2A;
        border-radius: 1.2rem;
        padding: 1rem 1.4rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        max-width: 80%;
    }
    
    .thinking-dots {
        display: flex;
        gap: 0.3rem;
    }
    
    .thinking-dot {
        width: 0.5rem;
        height: 0.5rem;
        background: #666;
        border-radius: 50%;
        animation: pulse 1.4s infinite;
    }
    
    .thinking-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .thinking-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    .thinking-text {
        color: #888;
        font-size: 0.9rem;
    }
    
    /* 反馈按钮区域 - 极简 */
    .feedback-container {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-start;
        margin-top: 0.3rem;
        margin-left: 0.5rem;
        opacity: 0.4;
        transition: opacity 0.2s;
    }
    
    .feedback-container:hover {
        opacity: 1;
    }
    
    .feedback-btn {
        background: none;
        border: none;
        color: #666;
        font-size: 0.8rem;
        cursor: pointer;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        transition: all 0.2s;
    }
    
    .feedback-btn:hover {
        color: #1976d2;
        background: #1A1A1A;
    }
    
    /* 来源折叠框 - 极简 */
    .source-item {
        background: #0A0A0A;
        padding: 0.5rem 0.8rem;
        border-radius: 0.5rem;
        margin: 0.3rem 0;
        color: #666;
        border-left: 2px solid #333;
        font-size: 0.8rem;
    }
    
    /* 输入区域 - 极简 */
    .input-section {
        max-width: 700px;
        margin: 2rem auto 0;
        padding: 0 1rem;
        position: relative;
    }
    
    .stTextInput input {
        background: #0F0F0F !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 2rem !important;
        padding: 0.8rem 1.2rem !important;
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
        transition: border-color 0.2s !important;
    }
    
    .stTextInput input:focus {
        border-color: #1976d2 !important;
        outline: none !important;
    }
    
    .stTextInput input::placeholder {
        color: #444 !important;
    }
    
    /* 发送按钮 - 极简 */
    .stButton > button {
        background: #1A1A1A !important;
        border: 1px solid #333 !important;
        border-radius: 2rem !important;
        color: #CCC !important;
        padding: 0.5rem 1.5rem !important;
        font-size: 0.9rem !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        border-color: #1976d2 !important;
        color: #1976d2 !important;
        background: #1A1A1A !important;
    }
    
    /* 隐私提示 - 底部小字 */
    .privacy-note {
        text-align: center;
        color: #333;
        font-size: 0.7rem;
        margin-top: 2rem;
        padding: 1rem;
        letter-spacing: 0.3px;
        border-top: 1px solid #1A1A1A;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
        30% { transform: translateY(-3px); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ========== 极简标题 ==========
st.markdown("""
<div class="title">
    🩺 医小管
    <span>AI辅导员 · 测试版</span>
</div>
""", unsafe_allow_html=True)

# ========== 极简侧边栏 ==========
with st.sidebar:
    st.markdown("### ⚡")
    if st.button("🗑️", help="清空对话"):
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 你好，我是医小管\n\n**你的专属AI辅导员**"}
        ]
        st.session_state.conversation_id = None
        st.session_state.show_thinking = False
        st.session_state.pending_question = None
        st.rerun()

# ========== 显示聊天历史 ==========
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# 显示所有历史消息
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
        
        # 反馈按钮
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
                    st.toast("👍 感谢反馈")
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
                    st.toast("👎 感谢反馈，我会努力改进")
        
        with col2:
            if st.button("📋", key=f"copy_{idx}", help="复制回答"):
                js = f"navigator.clipboard.writeText(`{message['content']}`);"
                st.components.v1.html(f"<script>{js}</script>", height=0)
                st.toast("已复制")
        
        # 来源
        if "sources" in message and message["sources"]:
            with st.expander("📚 来源"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"""
                    <div class="source-item">
                        <span>📄</span> {source[:150]}...
                    </div>
                    """, unsafe_allow_html=True)

# 如果正在思考，显示思考动画
if st.session_state.show_thinking:
    st.markdown("""
    <div class="thinking-container">
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
        placeholder="输入你的问题...",
        label_visibility="collapsed",
        key=input_key
    )

with col2:
    send_button = st.button("发送", use_container_width=True)

# ========== 发送逻辑 ==========
if (send_button or user_input) and user_input:
    # 检查是否已经在处理中
    if st.session_state.show_thinking:
        st.warning("正在处理上一个问题，请稍候...")
    else:
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.pending_question = user_input
        st.session_state.show_thinking = True
        st.session_state.input_key += 1
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ========== 处理AI回答（在页面底部，不显示在界面中） ==========
if st.session_state.show_thinking and st.session_state.pending_question:
    question = st.session_state.pending_question
    
    # 调用API
    result = st.session_state.llm.ask(question, st.session_state.conversation_id)
    
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
        question,
        reply,
        sources,
        session_id=st.session_state.conversation_id
    )
    
    # 添加AI回答
    st.session_state.messages.append({"role": "assistant", "content": reply, "sources": sources})
    
    # 重置状态
    st.session_state.show_thinking = False
    st.session_state.pending_question = None
    st.rerun()

# ========== 隐私提示 ==========
st.markdown("""
<div class="privacy-note">
    🛡️ 对话仅保存在本地 · 不上传个人信息 · 可随时清空
</div>
""", unsafe_allow_html=True)