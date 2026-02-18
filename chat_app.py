import streamlit as st
import time
from datetime import datetime
from llm_service import LLMService

# ========== 页面配置 ==========
st.set_page_config(
    page_title="医小管 AI辅导员",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== 初始化会话状态 ==========
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": """👋 你好，我是医小管

**你的专属AI辅导员**

---

💡 **试试问我：**
• 奖学金怎么申请？
• 医保报销比例？
• 考研有什么要求？
• 选课系统怎么进？

---"""
        }
    ]

if "llm" not in st.session_state:
    st.session_state.llm = LLMService()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "input_key" not in st.session_state:
    st.session_state.input_key = 0

if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

# ========== 深色模式CSS（极简高级） ==========
st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background: #0A0A0A;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 主容器 */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    /* 标题区域 */
    .title-section {
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .title-icon {
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        opacity: 0.9;
    }
    
    .title-main {
        font-size: 2.2rem;
        font-weight: 600;
        background: linear-gradient(135deg, #FFFFFF 0%, #A0A0A0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }
    
    .title-sub {
        color: #666666;
        font-size: 0.9rem;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    
    /* 聊天容器 */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem;
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
    
    /* 消息气泡 - 深色模式优化 */
    .message-bubble {
        max-width: 75%;
        padding: 1rem 1.4rem;
        border-radius: 1.5rem;
        position: relative;
        word-wrap: break-word;
        line-height: 1.6;
        font-size: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    .message-bubble.user {
        background: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3D3D3D;
        border-bottom-right-radius: 0.3rem;
    }
    
    .message-bubble.assistant {
        background: #1A1A1A;
        color: #E0E0E0;
        border: 1px solid #2A2A2A;
        border-bottom-left-radius: 0.3rem;
    }
    
    /* 消息内容样式 */
    .message-content {
        white-space: pre-wrap;
    }
    
    .message-content strong {
        color: #FFFFFF;
        font-weight: 600;
    }
    
    .message-content p {
        margin: 0.5rem 0;
    }
    
    /* 时间戳 */
    .timestamp {
        font-size: 0.7rem;
        color: #666666;
        margin-top: 0.5rem;
        text-align: right;
        letter-spacing: 0.3px;
    }
    
    .message-bubble.user .timestamp {
        color: #888888;
    }
    
    /* 来源信息样式 */
    .source-item {
        background: #1A1A1A;
        padding: 0.8rem 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        color: #A0A0A0;
        border: 1px solid #2A2A2A;
        font-size: 0.9rem;
        line-height: 1.5;
        transition: all 0.2s ease;
    }
    
    .source-item:hover {
        background: #202020;
        border-color: #3A3A3A;
    }
    
    .source-icon {
        color: #4A4A4A;
        margin-right: 0.5rem;
    }
    
    /* 输入区域 */
    .input-section {
        max-width: 800px;
        margin: 2rem auto 0;
        padding: 1rem;
    }
    
    /* 输入框容器 */
    .stTextInput {
        position: relative;
    }
    
    /* 输入框样式 - 深色模式 */
    .stTextInput input {
        background: #1A1A1A !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 2rem !important;
        padding: 1rem 1.5rem !important;
        font-size: 1rem !important;
        color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #404040 !important;
        background: #202020 !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
    }
    
    .stTextInput input::placeholder {
        color: #666666 !important;
        font-size: 0.95rem !important;
    }
    
    /* 隐藏输入框提示 */
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    
    /* 发送按钮 */
    .stButton > button {
        background: #2D2D2D !important;
        border: 1px solid #3D3D3D !important;
        border-radius: 2rem !important;
        padding: 1rem 2rem !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    
    .stButton > button:hover {
        background: #353535 !important;
        border-color: #454545 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
    }
    
    /* 加载动画 */
    .loading-container {
        display: flex;
        justify-content: flex-start;
        margin: 1.5rem 0;
    }
    
    .loading-indicator {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem 1.5rem;
        background: #1A1A1A;
        border-radius: 2rem;
        border: 1px solid #2A2A2A;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .loading-dots {
        display: flex;
        gap: 0.3rem;
    }
    
    .loading-dot {
        width: 0.5rem;
        height: 0.5rem;
        background: #666666;
        border-radius: 50%;
        animation: pulse 1.4s infinite;
    }
    
    .loading-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .loading-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    .loading-text {
        color: #888888;
        font-size: 0.9rem;
        letter-spacing: 0.3px;
    }
    
    /* 复制按钮 */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        padding: 0.3rem !important;
        color: #666666 !important;
        font-size: 1rem !important;
        box-shadow: none !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        color: #FFFFFF !important;
        background: transparent !important;
    }
    
    /* 动画 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
        30% { transform: translateY(-4px); opacity: 1; }
    }
    
    /* 分隔线 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #2A2A2A, transparent);
        margin: 2rem 0;
    }
    
    /* 侧边栏样式 */
    .sidebar-content {
        background: #0F0F0F;
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #2A2A2A;
    }
    
    /* 统计数字 */
    .metric-container {
        background: #1A1A1A;
        padding: 1rem;
        border-radius: 1rem;
        border: 1px solid #2A2A2A;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #FFFFFF;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #888888;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== 页面标题 ==========
st.markdown("""
<div class="title-section">
    <div class="title-icon">🩺</div>
    <div class="title-main">医小管</div>
    <div class="title-sub">AI辅导员 · 医药管理学院</div>
</div>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    st.markdown("### 💻 系统")
    
    # API连接状态
    if hasattr(st.session_state.llm, 'api_key') and st.session_state.llm.api_key:
        st.markdown("🟢 已连接")
    else:
        st.markdown("🔴 未连接")
    
    st.markdown("---")
    
    # 隐私说明
    st.markdown("### 🔒 隐私")
    st.markdown("对话仅保存在本地")
    
    st.markdown("---")
    
    # 对话统计
    st.markdown("### 📊 统计")
    user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
    assistant_msgs = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-value">{user_msgs}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">用户</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-value">{assistant_msgs}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">AI</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 清空按钮
    if st.button("🗑️ 清空", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "👋 你好，我是医小管"
            }
        ]
        st.session_state.conversation_id = None
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 聊天区域 ==========
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# 显示聊天历史
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f"""
        <div class="message-row user">
            <div class="message-bubble user">
                <div class="message-content">{message["content"]}</div>
                <div class="timestamp">{datetime.now().strftime("%H:%M")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([20, 1])
        with col1:
            st.markdown(f"""
            <div class="message-row assistant">
                <div class="message-bubble assistant">
                    <div class="message-content">{message["content"]}</div>
                    <div class="timestamp">{datetime.now().strftime("%H:%M")}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if "sources" in message and message["sources"]:
                with st.expander("📚 来源"):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"""
                        <div class="source-item">
                            <span class="source-icon">📄</span> {source[:150]}...
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📋", key=f"copy_{idx}"):
                js = f"navigator.clipboard.writeText(`{message['content']}`);"
                st.components.v1.html(f"<script>{js}</script>", height=0)
                st.toast("已复制")

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

if (send_button or user_input) and user_input and not st.session_state.is_loading:
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input
    })
    st.session_state.input_key += 1
    st.session_state.is_loading = True
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ========== 加载动画 ==========
if st.session_state.is_loading:
    last_message = st.session_state.messages[-1]
    
    st.markdown("""
    <div class="loading-container">
        <div class="loading-indicator">
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
            <span class="loading-text">医小管正在输入</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    result = st.session_state.llm.ask(
        last_message["content"], 
        st.session_state.conversation_id
    )
    
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
    
    st.session_state.is_loading = False
    
    message_data = {
        "role": "assistant",
        "content": reply
    }
    
    if sources:
        message_data["sources"] = sources
    
    st.session_state.messages.append(message_data)
    
    st.rerun()