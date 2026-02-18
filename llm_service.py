"""
大模型服务 - 调用千帆Agent
支持溯源功能，返回回答、会话ID和知识来源
适配Streamlit Secrets用于线上部署
优化AI回答：稳重亲切、清晰专业
"""

import requests
import re
import streamlit as st
import json

class LLMService:
    def __init__(self):
        """初始化 - 从st.secrets读取API Key"""
        try:
            self.api_key = st.secrets["BAIDU_API_KEY"]
            self.app_id = "3d1faab7-1cbf-4a77-8dd8-4f61947a8b57"  # ⚠️ 需要替换成你的真实应用ID
            
            if not self.api_key:
                st.error("❌ 未找到API Key，请检查Streamlit Secrets配置")
            
            self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
            
        except Exception as e:
            st.error(f"❌ 初始化失败: {e}")
            self.api_key = None
            self.app_id = None
    
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
    
    def ask(self, question, conversation_id=None):
        """向千帆Agent提问"""
        if not self.api_key:
            return "API Key未配置", None, []
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # ===== 稳重亲切风格的系统提示词 =====
        system_prompt = """你是一个医药管理学院的AI辅导员，名叫"医小管"。你的语气要专业稳重，像一位负责任的辅导员老师。

【重要：回答格式要求】
❌ 禁止使用 ###、##、* 等Markdown标题符号
❌ 禁止使用 ^[数字]^ 等引用标记
✅ 使用自然段落和数字序号（1. 2. 3.）来组织内容

【角色定位】
- 你是学校的官方辅导员助手，代表学校为学生服务
- 语气要稳重亲切，让学生感到被尊重和关心

【回答风格】
1. 用"同学"称呼对方，语气温和
2. 开头先问候，然后直接回答问题
3. 信息要完整准确，重要内容可以强调
4. 复杂问题可以分几点说明，用1. 2. 3.这样的序号
5. 结尾可以问"还有其他需要了解的吗？"

【示例】
同学你好。关于国家奖学金申请，我来为你说明一下。

申请的基本条件包括：综合素质测评排名前5%，无不及格科目。

申请流程主要有几个步骤：
1. 9月1日至15日提交申请表
2. 辅导员初步审核
3. 学院公开答辩评审
4. 学院公示2天
5. 学校最终评审并公示

申请时请准备好：申请表、成绩单、获奖证书复印件。

还有其他需要了解的吗？

记住：绝对不要用###这样的格式，要用自然流畅的语言！"""
        
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
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60
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
                
            else:
                error_msg = f"API调用失败: HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\n{json.dumps(error_detail, ensure_ascii=False)}"
                except:
                    pass
                
                return error_msg, None, []
                
        except requests.exceptions.Timeout:
            return "请求超时，请稍后再试", None, []
        except requests.exceptions.ConnectionError:
            return "网络连接失败，请检查网络", None, []
        except Exception as e:
            return f"错误：{str(e)}", None, []
    
    def _extract_sources(self, result):
        """提取知识来源"""
        sources = []
        
        if "citations" in result:
            citations = result["citations"]
            for c in citations:
                if isinstance(c, dict):
                    text = c.get("text", "")
                    if text:
                        sources.append(text)
        
        if not sources:
            if "answer" in result and result["answer"]:
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
            response = requests.get(
                "https://qianfan.baidubce.com/v2/apps",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                return f"获取失败: {response.status_code}"
        except Exception as e:
            return f"错误: {e}"