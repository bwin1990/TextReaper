import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from extract_literary import (
    OpenAIAdapter, DeepseekAdapter, 
    ErnieAdapter, QianwenAdapter,
    LiteraryExtractor
)

class TestInterface:
    def __init__(self, root, is_standalone=True):
        self.is_standalone = is_standalone
        
        # 如果是独立运行，使用root作为主窗口
        # 如果是嵌入式，使用root作为父框架
        if is_standalone:
            self.root = root
            self.root.title("AI模型测试界面")
            self.root.geometry("800x900")
            main_frame = ttk.Frame(root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            # 设置主窗口的网格权重
            root.grid_rowconfigure(0, weight=1)
            root.grid_columnconfigure(0, weight=1)
        else:
            self.root = root
            main_frame = ttk.Frame(self.root, padding="10")  # 创建新的Frame
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            # 设置Frame的网格权重
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
        
        # 设置main_frame的网格权重
        main_frame.grid_rowconfigure(6, weight=1)  # 让结果显示区域可以扩展
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 模型选择
        ttk.Label(main_frame, text="选择模型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="openai")
        models = ttk.Combobox(main_frame, textvariable=self.model_var)
        models['values'] = ('openai', 'deepseek', 'ernie', 'qianwen')
        models['state'] = 'readonly'
        models.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        models.bind('<<ComboboxSelected>>', self.on_model_change)
        
        # API密钥输入
        ttk.Label(main_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_key = tk.StringVar()
        self.api_entry = ttk.Entry(main_frame, textvariable=self.api_key, width=50)
        self.api_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Secret Key输入（用于文心一言）
        ttk.Label(main_frame, text="Secret Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.secret_key = tk.StringVar()
        self.secret_entry = ttk.Entry(main_frame, textvariable=self.secret_key, width=50)
        self.secret_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.secret_entry.grid_remove()  # 默认隐藏
        
        # System Prompt输入和模板控制
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(prompt_frame, text="System Prompt:").grid(row=0, column=0, sticky=tk.W)
        
        # Prompt模板选择
        self.prompt_templates = self.load_prompt_templates()
        self.template_var = tk.StringVar()
        self.template_combobox = ttk.Combobox(prompt_frame, textvariable=self.template_var, width=30)
        self.update_template_list()
        self.template_combobox.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.template_combobox.bind('<<ComboboxSelected>>', self.on_template_selected)
        
        # 模板操作按钮
        template_btn_frame = ttk.Frame(prompt_frame)
        template_btn_frame.grid(row=0, column=2, sticky=tk.E)
        
        ttk.Button(template_btn_frame, text="保存为模板", command=self.save_as_template).grid(row=0, column=0, padx=2)
        ttk.Button(template_btn_frame, text="删除模板", command=self.delete_template).grid(row=0, column=1, padx=2)
        
        self.system_prompt = scrolledtext.ScrolledText(prompt_frame, height=4, width=50)
        self.system_prompt.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.system_prompt.insert('1.0', "你是一个专业的文学鉴赏家，善于发现文本中富有文学性的句子。这些句子应该具有优美的意境、独特的比喻、生动的描写或深刻的哲理。")
        
        # 测试文本输入
        ttk.Label(main_frame, text="测试文本:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.test_text = scrolledtext.ScrolledText(main_frame, height=8, width=50)
        self.test_text.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 测试按钮
        ttk.Button(main_frame, text="运行测试", command=self.run_test).grid(row=5, column=0, columnspan=2, pady=10)
        
        # 结果显示
        ttk.Label(main_frame, text="提取结果:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.result_text = scrolledtext.ScrolledText(main_frame, height=12, width=50)
        self.result_text.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 加载配置
        self.load_config()
    
    def load_prompt_templates(self):
        """加载prompt模板"""
        try:
            with open('prompt_templates.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "默认文学提取": "你是一个专业的文学鉴赏家，善于发现文本中富有文学性的句子。这些句子应该具有优美的意境、独特的比喻、生动的描写或深刻的哲理。"
            }
    
    def save_prompt_templates(self):
        """保存prompt模板"""
        with open('prompt_templates.json', 'w', encoding='utf-8') as f:
            json.dump(self.prompt_templates, f, ensure_ascii=False, indent=4)
    
    def update_template_list(self):
        """更新模板列表"""
        self.template_combobox['values'] = tuple(self.prompt_templates.keys())
        if self.prompt_templates:
            self.template_combobox.set(next(iter(self.prompt_templates.keys())))
    
    def on_template_selected(self, event=None):
        """选择模板时的处理"""
        template_name = self.template_var.get()
        if template_name in self.prompt_templates:
            self.system_prompt.delete('1.0', tk.END)
            self.system_prompt.insert('1.0', self.prompt_templates[template_name])
    
    def save_as_template(self):
        """保存当前prompt为模板"""
        prompt_text = self.system_prompt.get('1.0', tk.END).strip()
        if not prompt_text:
            messagebox.showwarning("警告", "Prompt内容不能为空")
            return
        
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showwarning("警告", "请输入模板名称")
            return
        
        if template_name in self.prompt_templates:
            if not messagebox.askyesno("确认", f"模板 '{template_name}' 已存在，是否覆盖？"):
                return
        
        self.prompt_templates[template_name] = prompt_text
        self.save_prompt_templates()
        self.update_template_list()
        messagebox.showinfo("成功", "模板保存成功")
    
    def delete_template(self):
        """删除当前选中的模板"""
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showwarning("警告", "请选择要删除的模板")
            return
        
        if template_name not in self.prompt_templates:
            messagebox.showwarning("警告", "模板不存在")
            return
        
        if messagebox.askyesno("确认", f"确定要删除模板 '{template_name}' 吗？"):
            del self.prompt_templates[template_name]
            self.save_prompt_templates()
            self.update_template_list()
            messagebox.showinfo("成功", "模板删除成功")
    
    def load_config(self):
        """加载已保存的配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                model_configs = config.get('model_configs', {})
                current_model = self.model_var.get()
                if current_model in model_configs:
                    self.api_key.set(model_configs[current_model].get('api_key', ''))
                    if current_model == 'ernie':
                        self.secret_key.set(model_configs[current_model].get('secret_key', ''))
        except FileNotFoundError:
            pass
    
    def save_config(self):
        """保存当前配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {'model_configs': {}}
        
        current_model = self.model_var.get()
        config['model_configs'][current_model] = {
            'model_type': current_model,
            'api_key': self.api_key.get()
        }
        if current_model == 'ernie':
            config['model_configs'][current_model]['secret_key'] = self.secret_key.get()
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    
    def on_model_change(self, event=None):
        """模型变更时的处理"""
        current_model = self.model_var.get()
        if current_model == 'ernie':
            self.secret_entry.grid()
        else:
            self.secret_entry.grid_remove()
        self.load_config()
    
    def create_adapter(self):
        """创建模型适配器"""
        model_type = self.model_var.get()
        api_key = self.api_key.get()
        
        adapters = {
            'openai': lambda: OpenAIAdapter(api_key),
            'deepseek': lambda: DeepseekAdapter(api_key),
            'ernie': lambda: ErnieAdapter(api_key, self.secret_key.get()),
            'qianwen': lambda: QianwenAdapter(api_key)
        }
        
        return adapters[model_type]()
    
    def run_test(self):
        """运行测试"""
        try:
            # 保存当前配置
            self.save_config()
            
            # 创建适配器和提取器
            adapter = self.create_adapter()
            extractor = LiteraryExtractor(adapter)
            
            # 获取测试文本和system prompt
            test_text = self.test_text.get('1.0', tk.END).strip()
            system_prompt = self.system_prompt.get('1.0', tk.END).strip()
            
            if not test_text:
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert('1.0', "错误：请输入测试文本")
                return
            
            # 清空结果显示
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', "正在处理...\n")
            self.root.update()
            
            # 运行测试
            result = extractor.extract_literary_sentences(test_text, system_prompt)
            
            # 显示结果
            self.result_text.delete('1.0', tk.END)
            if result:
                self.result_text.insert('1.0', result)
            else:
                self.result_text.insert('1.0', "未找到文学性句子")
            
        except Exception as e:
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', f"错误：{str(e)}")

def main():
    root = tk.Tk()
    app = TestInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main() 