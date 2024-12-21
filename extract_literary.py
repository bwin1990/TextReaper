import os
import json
import time
from abc import ABC, abstractmethod
from typing import Optional
from openai import OpenAI
import dashscope
from http import HTTPStatus
import requests

class ModelAdapter(ABC):
    """模型适配器基类"""
    def __init__(self):
        self.system_prompt = "你是一个专业的文学鉴赏家，善于发现文本中富有文学性的句子。这些句子应该具有优美的意境、独特的比喻、生动的描写或深刻的哲理。"
    
    @abstractmethod
    def extract_sentences(self, text: str, system_prompt: str = None) -> str:
        """从文本中提取文学性句子"""
        pass

class OpenAIAdapter(ModelAdapter):
    """OpenAI模型适配器"""
    def __init__(self, api_key: str):
        super().__init__()
        self.client = OpenAI(api_key=api_key)
    
    def extract_sentences(self, text: str, system_prompt: str = None) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt or self.system_prompt},
                    {"role": "user", "content": f"请从以下文本中提取出具有文学性的句子，直接列出句子即可，每个句子单独一行：\n\n{text}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API调用出错: {str(e)}")
            return ""

class DeepseekAdapter(ModelAdapter):
    """Deepseek模型适配器"""
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
    
    def extract_sentences(self, text: str, system_prompt: str = None) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt or self.system_prompt},
                    {"role": "user", "content": f"请从以下文本中提取出具有文学性的句子，直接列出句子即可，每个句子单独一行：\n\n{text}"}
                ]
            }
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"Deepseek API调用失败: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Deepseek API调用出错: {str(e)}")
            return ""

class ErnieAdapter(ModelAdapter):
    """文心一言模型适配器"""
    def __init__(self, api_key: str, secret_key: str):
        super().__init__()
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = self._get_access_token()
    
    def _get_access_token(self) -> Optional[str]:
        """获取文心一言访问令牌"""
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json().get("access_token")
            return None
        except Exception as e:
            print(f"获取文心一言access_token失败: {str(e)}")
            return None
    
    def extract_sentences(self, text: str, system_prompt: str = None) -> str:
        if not self.access_token:
            print("文心一言access_token无效")
            return ""
        
        try:
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
            headers = {
                "Content-Type": "application/json"
            }
            params = {
                "access_token": self.access_token
            }
            data = {
                "messages": [
                    {"role": "system", "content": system_prompt or self.system_prompt},
                    {"role": "user", "content": f"请从以下文本中提取出具有文学性的句子，直接列出句子即可，每个句子单独一行：\n\n{text}"}
                ]
            }
            response = requests.post(url, headers=headers, params=params, json=data)
            if response.status_code == 200:
                return response.json()["result"].strip()
            else:
                print(f"文心一言API调用失败: {response.status_code}")
                return ""
        except Exception as e:
            print(f"文心一言API调用出错: {str(e)}")
            return ""

class QianwenAdapter(ModelAdapter):
    """通义千问模型适配器"""
    def __init__(self, api_key: str):
        super().__init__()
        dashscope.api_key = api_key
    
    def extract_sentences(self, text: str, system_prompt: str = None) -> str:
        try:
            response = dashscope.Generation.call(
                model='qwen-turbo',
                messages=[
                    {'role': 'system', 'content': system_prompt or self.system_prompt},
                    {'role': 'user', 'content': f'请从以下文本中提取出具有文学性的句子，直接列出句子即可，每个句子单独一行：\n\n{text}'}
                ]
            )
            if response.status_code == HTTPStatus.OK:
                return response.output.text.strip()
            else:
                print(f"通义千问API调用失败: {response.status_code}")
                return ""
        except Exception as e:
            print(f"通义千问API调用出错: {str(e)}")
            return ""

class LiteraryExtractor:
    """文学句子提取器"""
    def __init__(self, model_adapter: ModelAdapter):
        self.model_adapter = model_adapter
    
    def extract_literary_sentences(self, text: str, system_prompt: str = None) -> str:
        return self.model_adapter.extract_sentences(text, system_prompt)

def create_model_adapter(model_type: str, **kwargs) -> ModelAdapter:
    """
    创建模型适配器
    
    Args:
        model_type: 模型类型 ('openai', 'deepseek', 'ernie', 'qianwen')
        **kwargs: 模型所需的配置参数
    """
    adapters = {
        'openai': lambda: OpenAIAdapter(kwargs.get('api_key')),
        'deepseek': lambda: DeepseekAdapter(kwargs.get('api_key')),
        'ernie': lambda: ErnieAdapter(kwargs.get('api_key'), kwargs.get('secret_key')),
        'qianwen': lambda: QianwenAdapter(kwargs.get('api_key'))
    }
    
    adapter_creator = adapters.get(model_type.lower())
    if not adapter_creator:
        raise ValueError(f"不支持的模型类型: {model_type}")
    
    return adapter_creator()

class OutputManager:
    """输出管理器，处理不同的存储策略"""
    def __init__(self, output_dir: str, pdf_name: str, dump_interval: int = 10):
        self.output_dir = output_dir
        self.pdf_name = pdf_name
        self.dump_interval = dump_interval
        self.current_batch = []
        self.batch_count = 0
        self.temp_files = []
        
        # 创建PDF专属输出目录
        self.pdf_output_dir = os.path.join(output_dir, pdf_name)
        os.makedirs(self.pdf_output_dir, exist_ok=True)
    
    def add_content(self, page_number: int, content: str):
        """添加页面内容"""
        if content:
            self.current_batch.append((page_number, content))
    
    def _write_batch(self, filename: str, batch: list):
        """写入一批内容到文件"""
        with open(filename, "w", encoding="utf-8") as f:
            for page_num, content in sorted(batch, key=lambda x: x[0]):
                f.write(f"\n=== 第{page_num}页 ===\n")
                f.write(content)
                f.write("\n")
    
    def dump_interval_batch(self):
        """按间隔导出当前批次内容"""
        if not self.current_batch:
            return
            
        self.batch_count += 1
        temp_file = os.path.join(
            self.pdf_output_dir, 
            f"temp_batch_{self.batch_count:03d}.txt"
        )
        self._write_batch(temp_file, self.current_batch)
        self.temp_files.append(temp_file)
        self.current_batch = []
    
    def merge_and_cleanup(self, page_range: str = ""):
        """合并所有临时文件并清理"""
        if not self.temp_files and not self.current_batch:
            return
            
        # 处理最后一批数据
        if self.current_batch:
            self.dump_interval_batch()
        
        # 合并所有临时文件
        output_file = os.path.join(
            self.pdf_output_dir,
            f"{self.pdf_name}{page_range}_literary.txt"
        )
        
        with open(output_file, "w", encoding="utf-8") as outf:
            for temp_file in sorted(self.temp_files):
                with open(temp_file, "r", encoding="utf-8") as inf:
                    outf.write(inf.read())
                os.remove(temp_file)
        
        self.temp_files = []
    
    def append_to_file(self, page_number: int, content: str, page_range: str = ""):
        """直接追加内容到结果文件"""
        if not content:
            return
            
        output_file = os.path.join(
            self.pdf_output_dir,
            f"{self.pdf_name}{page_range}_literary.txt"
        )
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n=== 第{page_number}页 ===\n")
            f.write(content)
            f.write("\n")

def process_pages(
    model_config: dict, 
    start_page: int = None, 
    end_page: int = None, 
    storage_mode: str = "append",
    dump_interval: int = 10
):
    """
    处理指定范围的页面并提取文学性句子
    
    Args:
        model_config: 模型配置信息，包含模型类型和相关密钥
        start_page: 起始页码（从1开始），如果为None则从第一页开始
        end_page: 结束页码（包含），如果为None则处理到最后一页
        storage_mode: 存储模式，可选值：
            - "append": 边处理边追加到同一个文件（默认）
            - "batch": 按批次存储，最后合并
        dump_interval: 使用batch模式时，多少页保存一次
    """
    try:
        model_adapter = create_model_adapter(**model_config)
        extractor = LiteraryExtractor(model_adapter)
    except Exception as e:
        print(f"创建模型适配器失败: {str(e)}")
        return
    
    sep_pages_dir = "sep_pages"
    output_dir = "output"
    
    os.makedirs(output_dir, exist_ok=True)
    
    for pdf_dir in os.listdir(sep_pages_dir):
        pdf_path = os.path.join(sep_pages_dir, pdf_dir)
        if not os.path.isdir(pdf_path):
            continue
        
        # 获取所有页面文件并按数字顺序排序
        def get_page_number(filename):
            # 从文件名中提取页码数字
            try:
                return int(''.join(filter(str.isdigit, filename.split('_')[1].split('.')[0])))
            except (IndexError, ValueError):
                return 0
                
        page_files = [f for f in os.listdir(pdf_path) if f.endswith('.json')]
        page_files.sort(key=get_page_number)  # 按页码数字排序
        
        if not page_files:
            continue
            
        # 确定实际的起始和结束页码
        total_pages = len(page_files)
        actual_start = 1 if start_page is None else max(1, min(start_page, total_pages))
        actual_end = total_pages if end_page is None else min(end_page, total_pages)
        
        if actual_start > actual_end:
            print(f"错误：起始页码（{actual_start}）大于结束页码（{actual_end}）")
            continue
        
        # 创建输出管理器
        page_range = f"_pages_{actual_start}-{actual_end}"
        output_manager = OutputManager(output_dir, pdf_dir, dump_interval)
            
        print(f"正在处理书籍: {pdf_dir} (第{actual_start}页到第{actual_end}页)")
        
        # 创建页码到文件名的映射
        page_file_map = {get_page_number(f): f for f in page_files}
        
        pages_processed = 0
        # 只处理指定范围内的页面
        for current_page in range(actual_start, actual_end + 1):
            if current_page not in page_file_map:
                print(f"警告：找不到第{current_page}页的文件")
                continue
                
            page_file = page_file_map[current_page]
            page_path = os.path.join(pdf_path, page_file)
            
            with open(page_path, "r", encoding="utf-8") as f:
                page_data = json.load(f)
                
            print(f"正在处理页面 {current_page}")
            
            literary_sentences = extractor.extract_literary_sentences(page_data['content'])
            
            if storage_mode == "batch":
                # 批量模式：收集内容
                output_manager.add_content(current_page, literary_sentences)
                pages_processed += 1
                
                # 达到dump间隔时保存
                if pages_processed % dump_interval == 0:
                    output_manager.dump_interval_batch()
            else:
                # 追加模式：直接写入文件
                output_manager.append_to_file(
                    current_page, 
                    literary_sentences,
                    page_range
                )
            
            time.sleep(1)
        
        # 批量模式：最终合并所有文件
        if storage_mode == "batch":
            output_manager.merge_and_cleanup(page_range)
        
        print(f"完成处理: {pdf_dir} (第{actual_start}页到第{actual_end}页)")

if __name__ == "__main__":
    # 示例配置
    configs = {
        'openai': {
            'model_type': 'openai',
            'api_key': 'your-openai-api-key'
        },
        'deepseek': {
            'model_type': 'deepseek',
            'api_key': 'your-deepseek-api-key'
        },
        'ernie': {
            'model_type': 'ernie',
            'api_key': 'your-ernie-api-key',
            'secret_key': 'your-ernie-secret-key'
        },
        'qianwen': {
            'model_type': 'qianwen',
            'api_key': 'your-qianwen-api-key'
        }
    }
    
    # 选择要使用的模型配置
    model_config = configs['openai']  # 可以改为其他模型
    # 示例：处理第1页到第5页，使用批量存储模式
    process_pages(
        model_config, 
        start_page=1, 
        end_page=5,
        storage_mode="batch",
        dump_interval=2
    ) 