"""
医小管自我进化分析脚本
每周运行一次，生成优化建议清单
"""

import pandas as pd
import jieba
from collections import Counter
from datetime import datetime, timedelta
import os

class EvolutionAnalyzer:
    def __init__(self, log_file="evolution_logs.csv"):
        self.log_file = log_file
        self.df = None
        
    def load_data(self):
        """加载日志数据"""
        if not os.path.exists(self.log_file):
            print("❌ 暂无日志数据")
            return False
        
        self.df = pd.read_csv(self.log_file)
        print(f"✅ 加载了 {len(self.df)} 条对话记录")
        return True
    
    def analyze_high_frequency_questions(self, top_n=20):
        """分析高频问题关键词"""
        if self.df is None or len(self.df) == 0:
            return []
        
        questions = self.df['问题'].tolist()
        words = []
        for q in questions:
            # 使用jieba分词
            words.extend(jieba.lcut(str(q)))
        
        # 过滤停用词
        stop_words = ['的', '了', '是', '在', '有', '和', '与', '吗', 
                      '呢', '怎么', '如何', '什么', '为什么', '哪个', 
                      '可以', '需要', '申请', '办理']
        filtered_words = [w for w in words if len(w) > 1 and w not in stop_words]
        
        word_count = Counter(filtered_words)
        top_words = word_count.most_common(top_n)
        
        print(f"\n🔥 高频关键词 TOP{top_n}：")
        for word, count in top_words:
            print(f"  {word}: {count}次")
        
        return top_words
    
    def analyze_response_quality(self):
        """分析回答质量"""
        if self.df is None:
            return {}
        
        quality_stats = {}
        
        # 平均回答长度
        if '回答长度' in self.df.columns:
            quality_stats['avg_response_length'] = self.df['回答长度'].mean()
        
        # 平均来源数量
        if '来源数量' in self.df.columns:
            quality_stats['avg_sources'] = self.df['来源数量'].mean()
        
        # 无来源回答比例
        if '来源数量' in self.df.columns:
            no_source_pct = (self.df['来源数量'] == 0).mean() * 100
            quality_stats['no_source_pct'] = no_source_pct
        
        # 用户反馈统计
        if '用户反馈' in self.df.columns:
            like_count = (self.df['用户反馈'] == 'like').sum()
            dislike_count = (self.df['用户反馈'] == 'dislike').sum()
            total_feedback = like_count + dislike_count
            
            quality_stats['like_count'] = like_count
            quality_stats['dislike_count'] = dislike_count
            if total_feedback > 0:
                quality_stats['satisfaction_rate'] = like_count / total_feedback * 100
            else:
                quality_stats['satisfaction_rate'] = 0
        
        return quality_stats
    
    def analyze_bad_responses(self):
        """分析用户点踩的问题"""
        if self.df is None:
            return []
        
        bad_df = self.df[self.df['用户反馈'] == 'dislike']
        
        if len(bad_df) == 0:
            print("\n👍 暂无点踩记录，继续保持！")
            return []
        
        print(f"\n👎 用户点踩的问题（{len(bad_df)}条）：")
        bad_questions = []
        for _, row in bad_df.iterrows():
            print(f"  问题: {row['问题']}")
            print(f"  时间: {row['时间']}")
            bad_questions.append(row['问题'])
        
        return bad_questions
    
    def analyze_no_source_responses(self):
        """分析没有来源的回答"""
        if self.df is None:
            return []
        
        if '来源数量' not in self.df.columns:
            return []
        
        no_source_df = self.df[self.df['来源数量'] == 0]
        
        if len(no_source_df) == 0:
            print("\n📚 所有回答都有来源，很棒！")
            return []
        
        print(f"\n📚 需要补充知识库的问题（{len(no_source_df)}条）：")
        questions = []
        for _, row in no_source_df.head(10).iterrows():
            print(f"  问题: {row['问题']}")
            questions.append(row['问题'])
        
        return questions
    
    def analyze_performance(self):
        """分析性能指标"""
        if self.df is None:
            return {}
        
        perf_stats = {}
        
        if '响应时间(ms)' in self.df.columns:
            perf_stats['avg_response_time'] = self.df['响应时间(ms)'].mean()
            perf_stats['max_response_time'] = self.df['响应时间(ms)'].max()
            perf_stats['p95_response_time'] = self.df['响应时间(ms)'].quantile(0.95)
        
        return perf_stats
    
    def generate_optimization_todo(self):
        """生成知识库优化待办清单"""
        if not self.load_data():
            return
        
        suggestions = []
        
        # 1. 质量分析
        quality = self.analyze_response_quality()
        if quality:
            suggestions.append(f"## 质量报告")
            suggestions.append(f"- 平均回答长度: {quality.get('avg_response_length', 0):.1f}字")
            suggestions.append(f"- 平均来源数量: {quality.get('avg_sources', 0):.1f}条")
            suggestions.append(f"- 无来源回答比例: {quality.get('no_source_pct', 0):.1f}%")
            suggestions.append(f"- 用户满意度: {quality.get('satisfaction_rate', 0):.1f}%")
            suggestions.append("")
        
        # 2. 高频词建议
        top_words = self.analyze_high_frequency_questions(top_n=10)
        if top_words:
            suggestions.append(f"## 高频关键词（可能缺失的知识）")
            for word, count in top_words:
                if count > 3:
                    suggestions.append(f"- [ ] 需要补充关于「{word}」的知识文档（出现{count}次）")
            suggestions.append("")
        
        # 3. 点踩问题
        bad_questions = self.analyze_bad_responses()
        if bad_questions:
            suggestions.append(f"## 需要优化的回答")
            for q in bad_questions[:5]:
                suggestions.append(f"- [ ] 优化回答: {q[:50]}...")
            suggestions.append("")
        
        # 4. 无来源问题
        no_source = self.analyze_no_source_responses()
        if no_source:
            suggestions.append(f"## 需要补充知识库的问题")
            for q in no_source[:5]:
                suggestions.append(f"- [ ] 补充知识: {q[:50]}...")
            suggestions.append("")
        
        # 5. 性能分析
        perf = self.analyze_performance()
        if perf:
            suggestions.append(f"## 性能报告")
            suggestions.append(f"- 平均响应时间: {perf.get('avg_response_time', 0):.0f}ms")
            suggestions.append(f"- 95分位响应时间: {perf.get('p95_response_time', 0):.0f}ms")
            if perf.get('p95_response_time', 0) > 5000:
                suggestions.append(f"- [ ] 响应时间过长，建议优化知识库检索")
        
        # 生成Markdown格式的待办清单
        filename = f"kb_optimization_{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 📚 医小管知识库优化清单\n\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            for s in suggestions:
                f.write(f"{s}\n")
        
        print(f"\n✅ 已生成优化清单：{filename}")
        return suggestions


def main():
    print("="*60)
    print("🧬 医小管自我进化分析系统 v2.0")
    print("="*60)
    
    analyzer = EvolutionAnalyzer()
    
    # 生成优化清单
    analyzer.generate_optimization_todo()
    
    # 显示简要统计
    if analyzer.df is not None:
        print("\n📊 简要统计：")
        print(f"总对话数: {len(analyzer.df)}")
        
        # 按日期统计
        if '时间' in analyzer.df.columns:
            analyzer.df['日期'] = pd.to_datetime(analyzer.df['时间']).dt.date
            daily = analyzer.df.groupby('日期').size()
            print(f"日均对话: {daily.mean():.1f}条")


if __name__ == "__main__":
    main()