"""
大模型服务 - 调用千帆Agent
紧急版本：强制每秒最多1次请求，确保不触发限流
"""

import requests
import re
import streamlit as st
import json
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class LLMService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式，确保所有用户共享同一个实例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        """初始化 - 只执行一次"""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            
            try:
                self.api_key = st.secrets["BAIDU_API_KEY"]
                self.app_id = "3d1faab7-1cbf-4a77-8dd8-4f61947a8b57"  # 你的应用ID
                
                if not self.api_key:
                    st.error("❌ 未找到API Key，请检查Streamlit Secrets配置")
                
                self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
                
                # 创建带重试机制的会话
                self.session = self._create_retry_session()
                
                # ===== 限流控制参数 =====
                self.last_request_time = 0  # 上次请求时间
                self.request_interval = 1.2  # 强制每秒最多0.8次（1.2秒间隔）
                self.request_queue = []  # 请求队列
                self.processing = False  # 是否正在处理
                
                # 启动队列处理线程
                self._start_queue_processor()
                
            except Exception as e:
                st.error(f"❌ 初始化失败: {e}")
                self.api_key = None
                self.app_id = None
    
    def _start_queue_processor(self):
        """启动队列处理线程"""
        import threading
        import time
        
        def process_queue():
            while True:
                if self.request_queue and not self.processing:
                    self.processing = True
                    # 取出请求
                    question, conversation_id, callback = self.request_queue.pop(0)
                    
                    # 强制等待，确保不超过QPS限制
                    current_time = time.time()
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < self.request_interval:
                        wait_time = self.request_interval - time_since_last
                        time.sleep(wait_time)
                    
                    # 调用API
                    try:
                        result = self._make_request(question, conversation_id)
                        callback(result)
                    except Exception as e:
                        callback((f"错误: {str(e)}", None, []))
                    
                    self.last_request_time = time.time()
                    self.processing = False
                
                time.sleep(0.1)  # 避免CPU空转
        
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
    
    def _create_retry_session(self, retries=3, backoff_factor=0.5):
        """创建带重试机制的requests会话"""
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def _clean_answer(self, answer):
        """清理回答中的引用标记"""
        if not answer:
            return answer
        
        cleaned = re.sub(r'\^\[\d+\]\^', '', answer)
        cleaned = re.sub(r'\[\d+\]', '', cleaned)
        cleaned = re.sub(r'\^(\[\d+\])+\^', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def _make_request(self, question, conversation_id):
        """实际发起API请求"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        system_prompt = """你是一个医药管理学院的AI辅导员，名叫"医小管"。你的语气要专业稳重，像一位负责任的辅导员老师。"""
        
        data = {
            "app_id": self.app_id,
            "query": question,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        # 发送请求
        response = self.session.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=(10, 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            new_conversation_id = result.get("conversation_id")
            cleaned_answer = self._clean_answer(answer)
            sources = self._extract_sources(result)
            return cleaned_answer, new_conversation_id, sources
        else:
            error_msg = f"API调用失败: HTTP {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f"\n{json.dumps(error_detail, ensure_ascii=False)}"
            except:
                pass
            return error_msg, None, []
    
    def ask(self, question, conversation_id=None):
        """
        向千帆Agent提问（使用队列排队）
        """
        if not self.api_key:
            return "API Key未配置", None, []
        
        # 创建一个事件来等待结果
        from threading import Event
        
        result_event = Event()
        result_container = []
        
        def callback(result):
            result_container.append(result)
            result_event.set()
        
        # 将请求加入队列
        self.request_queue.append((question, conversation_id, callback))
        
        # 等待结果（最多等待30秒）
        result_event.wait(timeout=30)
        
        if result_container:
            return result_container[0]
        else:
            return "请求超时，请稍后再试", None, []
    
    def _extract_sources(self, result):
        """提取知识来源"""
        sources = []
        
        if "citations" in result:
            citations = result["citations"]
            for c in citations:
                if isinstance(c, dict):
                    text = c.get("text", "")
                    if text and len(text) > 10:
                        sources.append(text)
        
        if not sources and "answer" in result and result["answer"]:
            sources.append("📚 回答基于学校知识库")
        
        # 去重
        seen = set()
        unique_sources = []
        for s in sources:
            if s not in seen and len(s) > 10:
                seen.add(s)
                unique_sources.append(s)
        
        return unique_sources
    
    def get_app_info(self):
        """获取应用信息（测试用）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = self.session.get(
                "https://qianfan.baidubce.com/v2/apps",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return f"获取失败: {response.status_code}"
        except Exception as e:
            return f"错误: {e}"