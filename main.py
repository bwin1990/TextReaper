import os
import json
import shutil
from tkinter import filedialog
from extract_literary import process_pages
from pdf_parse import process_all_pdfs, parse_pdf
import tkinter as tk

def load_config(config_file: str = 'config.json') -> dict:
    """
    加载配置文件
    如果配置文件不存在，创建默认配置
    """
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认配置
    default_config = {
        'model_configs': {
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
        },
        'default_model': 'openai'  # 默认使用的模型
    }
    
    # 保存默认配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    
    return default_config

def select_pdf_files():
    """
    选择PDF文件
    返回：选择的PDF文件路径列表
    """
    def open_file_dialog():
        """打开文件选择对话框"""
        root = tk.Tk()
        root.attributes('-topmost', True)  # 窗口置顶
        root.withdraw()  # 隐藏主窗口
        try:
            files = filedialog.askopenfilenames(
                parent=root,
                title="选择PDF文件",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            return list(files)
        finally:
            root.destroy()
    
    while True:
        print("\n请选择PDF文件来源：")
        print("1. 从pdf_books目录选择")
        print("2. 从系统选择")
        print("3. 退出")
        
        choice = input("请输入选项 [1/2/3]: ").strip()
        
        if choice == "3":
            return None
            
        if choice == "1":
            # 从pdf_books目录选择
            pdf_files = [f for f in os.listdir('pdf_books') if f.lower().endswith('.pdf')]
            if not pdf_files:
                print("警告：pdf_books目录中没有找到PDF文件")
                continue
                
            print("\n找到以下PDF文件：")
            for i, pdf in enumerate(pdf_files, 1):
                print(f"{i}. {pdf}")
                
            while True:
                try:
                    selection = input("\n请输入文件编号（多个文件用逗号分隔，直接回车选择全部）: ").strip()
                    if not selection:
                        return [os.path.join('pdf_books', f) for f in pdf_files]
                        
                    indices = [int(i.strip()) for i in selection.split(',')]
                    selected_files = []
                    for idx in indices:
                        if 1 <= idx <= len(pdf_files):
                            selected_files.append(os.path.join('pdf_books', pdf_files[idx-1]))
                        else:
                            print(f"警告：编号 {idx} 无效，已忽略")
                    
                    if selected_files:
                        return selected_files
                    print("请选择有效的文件编号")
                except ValueError:
                    print("请输入有效的数字")
                    
        elif choice == "2":
            # 从系统选择
            try:
                files = open_file_dialog()
                if not files:
                    print("未选择任何文件")
                    continue
                
                # 复制选择的文件到pdf_books目录
                pdf_books_dir = 'pdf_books'
                os.makedirs(pdf_books_dir, exist_ok=True)
                
                copied_files = []
                for file_path in files:
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(pdf_books_dir, filename)
                    
                    # 如果文件已存在，询问是否覆盖
                    if os.path.exists(dest_path):
                        overwrite = input(f"\n文件 {filename} 已存在，是否覆盖？[y/N]: ").strip().lower()
                        if overwrite != 'y':
                            print(f"已跳过 {filename}")
                            continue
                    
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(dest_path)
                    print(f"已复制: {filename}")
                
                if copied_files:
                    return copied_files
            except Exception as e:
                print(f"选择文件时出错: {str(e)}")
                continue
        else:
            print("请输入有效的选项")

def main():
    # 加载配置
    config = load_config()
    
    # 获取要使用的模型配置
    model_name = input("请选择要使用的模型 (openai/deepseek/ernie/qianwen) [默认: openai]: ").strip().lower()
    if not model_name:
        model_name = config['default_model']
    
    if model_name not in config['model_configs']:
        print(f"错误：不支持的模型类型 {model_name}")
        return
    
    model_config = config['model_configs'][model_name]
    
    # 检查API密钥是否已配置
    if model_config['api_key'] == f'your-{model_name}-api-key':
        api_key = input(f"请输入{model_name}的API密钥: ").strip()
        if not api_key:
            print("错误：API密钥不能为空")
            return
        model_config['api_key'] = api_key
        
        # 如果是文心一言，还需要secret_key
        if model_name == 'ernie' and model_config['secret_key'] == 'your-ernie-secret-key':
            secret_key = input("请输入文心一言的Secret Key: ").strip()
            if not secret_key:
                print("错误：Secret Key不能为空")
                return
            model_config['secret_key'] = secret_key
        
        # 保存更新后的配置
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    
    # 检查必要的目录是否存在
    required_dirs = ['pdf_books', 'sep_pages', 'output']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"创建目录: {dir_name}")
    
    # 选择PDF文件
    selected_files = select_pdf_files()
    if not selected_files:
        print("未选择任何文件，程序退出")
        return
    
    # 处理选择的PDF文件
    print("\n开始解析PDF文件...")
    for pdf_path in selected_files:
        filename = os.path.basename(pdf_path)
        print(f"正在处理: {filename}")
        try:
            parse_pdf(pdf_path, "sep_pages")
            print(f"完成解析: {filename}")
        except Exception as e:
            print(f"处理 {filename} 时出错: {str(e)}")
            continue
    
    # 获取存储模式
    while True:
        storage_mode = input("\n请选择存储模式:\n1. 边处理边追加到同一个文件（默认）\n2. 按批次存储并最终合并\n请输入选项 [1/2]: ").strip()
        if not storage_mode or storage_mode == "1":
            storage_mode = "append"
            dump_interval = 10  # 默认值，实际不会使用
            break
        elif storage_mode == "2":
            storage_mode = "batch"
            while True:
                try:
                    dump_interval = int(input("请输入每多少页保存一次 [默认: 10]: ").strip() or "10")
                    if dump_interval > 0:
                        break
                    print("请输入大于0的数字")
                except ValueError:
                    print("请输入有效的数字")
            break
        else:
            print("请输入有效的选项")
    
    # 获取页码范围
    while True:
        page_range = input("\n请输入要处理的页码范围（格式：起始页-结束页，直接回车处理全部页面）: ").strip()
        if not page_range:
            start_page = None
            end_page = None
            break
        
        try:
            if '-' in page_range:
                start, end = map(int, page_range.split('-'))
                if start > 0 and end >= start:
                    start_page = start
                    end_page = end
                    break
            print("格式错误，请使用正确的格式（例如：1-5）或直接回车处理全部页面")
        except ValueError:
            print("请输入有效的数字范围")
    
    print(f"\n使用 {model_name} 模型开始处理" + 
          (f"第{start_page}页到第{end_page}页..." if start_page else "所有页面..."))
    
    try:
        process_pages(
            model_config, 
            start_page=start_page, 
            end_page=end_page,
            storage_mode=storage_mode,
            dump_interval=dump_interval if storage_mode == "batch" else 10
        )
        print("处理完成！")
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main() 