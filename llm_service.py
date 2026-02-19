"""
大模型服务 - 调用千帆Agent
支持重试、缓存、稳定性优化和自我进化数据收集
"""

import requests
import re
import streamlit as st
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class LLMService:
    def __init__(self):
        """初始化 - 从st.secrets读取API Key"""
        try:
            self.api_key = st.secrets["BAIDU_API_KEY"]
            self.app_id = "3d1faab7-1cbf-4a77-8dd8-4f61947a8b57"  # 你的应用ID
            
            if not self.api_key:
                st.error("❌ 未找到API Key，请检查Streamlit Secrets配置")
            
            self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
            
            # 创建带重试机制的会话
            self.session = self._create_retry_session()
            
        except Exception as e:
            st.error(f"❌ 初始化失败: {e}")
            self.api_key = None
            self.app_id = None
    
    def _create_retry_session(self, retries=3, backoff_factor=0.5):
        """
        创建带重试机制的requests会话
        retries: 重试次数
        backoff_factor: 重试间隔因子
        """
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],  # 遇到这些HTTP状态码时重试
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
        cleaned = cleaned.strip()
        
        return cleaned
    
    def ask(self, question, conversation_id=None, max_retries=3):
        """
        向千帆Agent提问（带重试和稳定性优化）
        
        Args:
            question: 用户问题
            conversation_id: 会话ID（用于多轮对话）
            max_retries: 最大重试次数
        
        Returns:
            tuple: (回答内容, 新的会话ID, 来源列表)
        """
        if not self.api_key:
            return "API Key未配置", None, []
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 稳重亲切风格的系统提示词
        system_prompt = """你是一个医药管理学院的AI辅导员，名叫"医小管"。你的语气要专业稳重，像一位负责任的辅导员老师。

【回答风格】
1. 用"同学"称呼对方，语气温和
2. 开头先问候，然后直接回答问题
3. 信息要完整准确，重要内容可以适当强调
4. 复杂问题可以分几点说明，但不要用Markdown符号
5. 结尾可以问"还有其他需要了解的吗？"

【示例】
同学你好，关于国家奖学金申请，我来为你说明一下。

申请的基本条件包括：综合素质测评排名前5%，无不及格科目。

申请流程主要有几个步骤：
第一，9月1日至15日提交申请表。
第二，辅导员初步审核。
第三，学院公开答辩评审。
第四，学院公示2天。
第五，学校最终评审并公示。

申请时请准备好：申请表、成绩单、获奖证书复印件。

还有其他需要了解的吗？"""
        
        # 构建请求体
        data = {
            "app_id": self.app_id,
            "query": question,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        # 重试逻辑
        for attempt in range(max_retries):
            try:
                # 使用带重试的会话发送请求
                response = self.session.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=(10, 30)  # (连接超时, 读取超时)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    answer = result.get("answer", "")
                    new_conversation_id = result.get("conversation_id")
                    
                    # 清理引用标记
                    cleaned_answer = self._clean_answer(answer)
                    
                    # 提取来源
                    sources = self._extract_sources(result)
                    
                    return cleaned_answer, new_conversation_id, sources
                    
                elif response.status_code in [429, 500, 502, 503, 504]:
                    # 这些错误值得重试
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数退避：1, 2, 4秒
                        time.sleep(wait_time)
                        continue
                    else:
                        error_msg = f"服务暂时不可用，请稍后再试 (HTTP {response.status_code})"
                        return error_msg, None, []
                else:
                    error_msg = f"API调用失败: HTTP {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f"\n{json.dumps(error_detail, ensure_ascii=False)}"
                    except:
                        pass
                    
                    return error_msg, None, []
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    return "请求超时，请稍后再试", None, []
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    return "网络连接失败，请检查网络", None, []
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    return f"错误：{str(e)}", None, []
        
        return "服务暂时不可用，请稍后再试", None, []
    
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