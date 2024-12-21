import os
import json
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from extract_literary import (
    OpenAIAdapter, DeepseekAdapter, 
    ErnieAdapter, QianwenAdapter,
    LiteraryExtractor, process_pages
)
from pdf_parse import parse_pdf
from epub_parse import parse_epub
from test_interface import TestInterface  # 导入测试界面类

class MainInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("文学句子提取工具")
        self.root.geometry("900x800")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置主窗口的网格权重
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # 设置主框架的网格权重
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # PDF处理页面
        self.pdf_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pdf_frame, text="PDF处理")
        
        # 测试页面
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text="模型测试")
        
        # 设置PDF处理页面的组件
        self.setup_pdf_page()
        
        # 设置测试页面
        self.setup_test_page()
        
        # 加载配置
        self.load_config()
    
    def setup_pdf_page(self):
        """设置PDF处理页面的组件"""
        # 设置pdf_frame的网格权重
        self.pdf_frame.grid_rowconfigure(3, weight=1)  # 日志区域可扩展
        self.pdf_frame.grid_columnconfigure(0, weight=1)
        
        # 模型配置区域
        self.setup_model_section(self.pdf_frame)
        
        # PDF文件选择区域
        self.setup_pdf_section(self.pdf_frame)
        
        # 处理选项区域
        self.setup_process_section(self.pdf_frame)
        
        # 日志显示区域
        self.setup_log_section(self.pdf_frame)
    
    def setup_test_page(self):
        """设置测试页面"""
        # 创建TestInterface实例，但使用test_frame作为根窗口
        self.test_interface = TestInterface(self.test_frame, is_standalone=False)
    
    def setup_model_section(self, parent):
        """设置模型配置区域"""
        model_frame = ttk.LabelFrame(parent, text="模型配置", padding="5")
        model_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 模型选择
        ttk.Label(model_frame, text="选择模型:").grid(row=0, column=0, sticky=tk.W)
        self.model_var = tk.StringVar(value="openai")
        models = ttk.Combobox(model_frame, textvariable=self.model_var)
        models['values'] = ('openai', 'deepseek', 'ernie', 'qianwen')
        models['state'] = 'readonly'
        models.grid(row=0, column=1, sticky=(tk.W, tk.E))
        models.bind('<<ComboboxSelected>>', self.on_model_change)
        
        # API密钥输入
        ttk.Label(model_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.api_key = tk.StringVar()
        self.api_entry = ttk.Entry(model_frame, textvariable=self.api_key, width=50)
        self.api_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Secret Key输入（用于文心一言）
        ttk.Label(model_frame, text="Secret Key:").grid(row=2, column=0, sticky=tk.W)
        self.secret_key = tk.StringVar()
        self.secret_entry = ttk.Entry(model_frame, textvariable=self.secret_key, width=50)
        self.secret_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
        self.secret_entry.grid_remove()

    def setup_pdf_section(self, parent):
        """设置文件选择区域"""
        file_frame = ttk.LabelFrame(parent, text="文件选择", padding="5")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 文件列表
        self.file_listbox = tk.Listbox(file_frame, height=6, selectmode=tk.MULTIPLE)
        self.file_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 按钮区
        ttk.Button(file_frame, text="从系统选择", command=self.select_system_files).grid(row=1, column=0, pady=5)
        ttk.Button(file_frame, text="刷新列表", command=self.refresh_file_list).grid(row=1, column=1, pady=5)

    def setup_process_section(self, parent):
        """设置处理选项区域"""
        process_frame = ttk.LabelFrame(parent, text="处理选项", padding="5")
        process_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 存储模式
        ttk.Label(process_frame, text="存储模式:").grid(row=0, column=0, sticky=tk.W)
        self.storage_mode = tk.StringVar(value="append")
        ttk.Radiobutton(process_frame, text="边处理边追加", value="append", 
                       variable=self.storage_mode).grid(row=0, column=1)
        ttk.Radiobutton(process_frame, text="按批次存储", value="batch", 
                       variable=self.storage_mode).grid(row=0, column=2)
        
        # 批次大小
        ttk.Label(process_frame, text="批次大小:").grid(row=1, column=0, sticky=tk.W)
        self.batch_size = tk.StringVar(value="10")
        ttk.Entry(process_frame, textvariable=self.batch_size, width=10).grid(row=1, column=1)
        
        # 页码范围
        ttk.Label(process_frame, text="页码范围:").grid(row=2, column=0, sticky=tk.W)
        self.page_range = tk.StringVar()
        ttk.Entry(process_frame, textvariable=self.page_range, width=20).grid(row=2, column=1)
        ttk.Label(process_frame, text="(格式: 起始页-结束页，留空处理全部)").grid(row=2, column=2)
        
        # 开始处理按钮
        ttk.Button(process_frame, text="开始处理", command=self.start_processing).grid(row=3, column=0, columnspan=3, pady=10)

    def setup_log_section(self, parent):
        """设置日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="处理日志", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置日志区域可扩展
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

    def load_config(self):
        """加载配置文件"""
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
        """保存配置"""
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
        """模型变更处理"""
        current_model = self.model_var.get()
        if current_model == 'ernie':
            self.secret_entry.grid()
        else:
            self.secret_entry.grid_remove()
        self.load_config()

    def select_system_files(self):
        """从系统选择文件"""
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[
                ("支持的文件", "*.pdf *.epub"),
                ("PDF文件", "*.pdf"),
                ("EPUB文件", "*.epub"),
                ("所有文件", "*.*")
            ]
        )
        if not files:
            return
        
        # 复制文件到books目录
        os.makedirs('books', exist_ok=True)
        for file_path in files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join('books', filename)
            
            if os.path.exists(dest_path):
                if not tk.messagebox.askyesno("文件已存在", 
                    f"文件 {filename} 已存在，是否覆盖？"):
                    continue
            
            shutil.copy2(file_path, dest_path)
            self.log(f"已复制: {filename}")
        
        self.refresh_file_list()

    def refresh_file_list(self):
        """刷新文件列表"""
        self.file_listbox.delete(0, tk.END)
        if os.path.exists('books'):
            for file in sorted(os.listdir('books')):
                if file.lower().endswith(('.pdf', '.epub')):
                    self.file_listbox.insert(tk.END, file)

    def start_processing(self):
        """开始处理文件"""
        # 获取选中的文件
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            tk.messagebox.showwarning("警告", "请选择要处理的文件")
            return
        
        # 创建模型配置
        model_config = {
            'model_type': self.model_var.get(),
            'api_key': self.api_key.get()
        }
        if model_config['model_type'] == 'ernie':
            model_config['secret_key'] = self.secret_key.get()
        
        # 解析页码范围
        start_page = None
        end_page = None
        page_range = self.page_range.get().strip()
        if page_range:
            try:
                start, end = map(int, page_range.split('-'))
                if start > 0 and end >= start:
                    start_page = start
                    end_page = end
                else:
                    tk.messagebox.showerror("错误", "无效的页码范围")
                    return
            except ValueError:
                tk.messagebox.showerror("错误", "页码范围格式错误")
                return
        
        # 处理选中的文件
        for idx in selected_indices:
            filename = self.file_listbox.get(idx)
            file_path = os.path.join('books', filename)
            
            try:
                self.log(f"\n开始处理: {filename}")
                
                # 根据文件类型选择解析方法
                if filename.lower().endswith('.pdf'):
                    self.log("正在解析PDF...")
                    parse_pdf(file_path, "sep_pages")
                else:  # epub
                    self.log("正在解析EPUB...")
                    parse_epub(file_path, "sep_pages")
                
                # 提取文学句子
                self.log("开始提取文学句子...")
                process_pages(
                    model_config,
                    start_page=start_page,
                    end_page=end_page,
                    storage_mode=self.storage_mode.get(),
                    dump_interval=int(self.batch_size.get())
                )
                
                self.log(f"完成处理: {filename}")
            except Exception as e:
                self.log(f"处理出错: {str(e)}")
                tk.messagebox.showerror("错误", f"处理 {filename} 时出错:\n{str(e)}")

    def log(self, message):
        """添加日志信息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

def main():
    root = tk.Tk()
    app = MainInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main() 