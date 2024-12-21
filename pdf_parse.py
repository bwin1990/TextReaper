import os
import fitz  # PyMuPDF
import json

def parse_pdf(pdf_path, output_dir):
    """
    解析PDF文件并将每页内容保存到单独的JSON文件中，
    同时处理跨页文本问题
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录路径
    """
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    
    # 获取PDF文件名（不含扩展名）
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # 为每个PDF创建单独的目录
    pdf_output_dir = os.path.join(output_dir, pdf_name)
    os.makedirs(pdf_output_dir, exist_ok=True)
    
    # 计算页码宽度（用于生成固定宽度的页码）
    total_pages = len(doc)
    page_number_width = len(str(total_pages))
    
    # 存储所有页面的文本，用于处理跨页文本
    all_pages_text = []
    
    # 第一遍：收集所有页面的文本
    print(f"正在提取文本，总页数：{total_pages}")
    for page_num in range(total_pages):
        try:
            page = doc[page_num]
            text = page.get_text()
            all_pages_text.append(text.strip())
            if (page_num + 1) % 10 == 0:
                print(f"已处理 {page_num + 1} 页")
        except Exception as e:
            print(f"提取第 {page_num + 1} 页文本时出错: {str(e)}")
            all_pages_text.append("")  # 添加空文本作为占位符
    
    # 第二遍：处理文本并保存，考虑跨页情况
    print("\n正在处理跨页文本...")
    for page_num in range(total_pages):
        try:
            current_text = all_pages_text[page_num]
            
            # 处理跨页文本
            # 如果不是第一页，检查上一页的最后一段
            if page_num > 0 and current_text and all_pages_text[page_num - 1]:
                prev_text = all_pages_text[page_num - 1]
                # 如果上一页的最后一个字符不是标点符号，可能存在跨页
                if prev_text and not prev_text[-1] in '。！？.!?':
                    # 获取上一页的最后一段
                    prev_paragraphs = prev_text.split('\n')
                    last_paragraph = prev_paragraphs[-1] if prev_paragraphs else ""
                    # 将上一页的最后一段添加到当前页的开头
                    if last_paragraph:
                        current_text = last_paragraph + current_text
            
            # 如果不是最后一页，检查下一页的第一段
            if page_num < total_pages - 1 and current_text and all_pages_text[page_num + 1]:
                next_text = all_pages_text[page_num + 1]
                # 如果当前页的最后一个字符不是标点符号，可能存在跨页
                if current_text and not current_text[-1] in '。！？.!?':
                    # 获取下一页的第一段
                    next_paragraphs = next_text.split('\n')
                    first_paragraph = next_paragraphs[0] if next_paragraphs else ""
                    # 将下一页的第一段添加到当前页的结尾
                    if first_paragraph:
                        current_text = current_text + first_paragraph
            
            # 创建包含页面信息的字典
            page_data = {
                "page_number": page_num + 1,
                "content": current_text,
                "source_pdf": pdf_name,
                "total_pages": total_pages
            }
            
            # 使用固定宽度的页码格式保存文件
            output_file = os.path.join(
                pdf_output_dir, 
                f"page_{str(page_num + 1).zfill(page_number_width)}.json"
            )
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(page_data, f, ensure_ascii=False, indent=4)
            
            if (page_num + 1) % 10 == 0:
                print(f"已保存 {page_num + 1} 页")
                
        except Exception as e:
            print(f"处理第 {page_num + 1} 页时出错: {str(e)}")
            # 保存空内容，确保页面完整性
            page_data = {
                "page_number": page_num + 1,
                "content": "",
                "source_pdf": pdf_name,
                "total_pages": total_pages
            }
            output_file = os.path.join(
                pdf_output_dir, 
                f"page_{str(page_num + 1).zfill(page_number_width)}.json"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(page_data, f, ensure_ascii=False, indent=4)
    
    doc.close()
    print("PDF处理完成")

def process_all_pdfs():
    """处理pdf_books目录下的所有PDF文件"""
    pdf_dir = "pdf_books"
    output_dir = "sep_pages"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历所有PDF文件
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            print(f"正在处理: {filename}")
            try:
                parse_pdf(pdf_path, output_dir)
                print(f"完成处理: {filename}")
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")

if __name__ == "__main__":
    process_all_pdfs() 