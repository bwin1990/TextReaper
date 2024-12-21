import os
import json
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict

def clean_html_content(html_content: str) -> str:
    """清理HTML内容，提取纯文本"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # 移除script和style标签
    for script in soup(["script", "style"]):
        script.decompose()
    # 获取文本
    text = soup.get_text()
    # 清理空白字符
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def split_content(text: str, chunk_size: int = 2000) -> List[str]:
    """将文本按照指定大小分块
    
    Args:
        text: 要分割的文本
        chunk_size: 每块的大致字符数
        
    Returns:
        分割后的文本块列表
    """
    # 首先按段落分割
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        if current_size + para_size > chunk_size and current_chunk:
            # 当前块已满，保存并开始新的块
            chunks.append('\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            # 添加到当前块
            current_chunk.append(para)
            current_size += para_size
    
    # 处理最后一个块
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def parse_epub(epub_path: str, output_dir: str = "sep_pages") -> Dict[str, List[Dict]]:
    """解析EPUB文件并按块保存内容
    
    Args:
        epub_path: EPUB文件路径
        output_dir: 输出目录
        
    Returns:
        解析结果的信息
    """
    # 创建输出目录
    book_name = os.path.splitext(os.path.basename(epub_path))[0]
    book_dir = os.path.join(output_dir, book_name)
    os.makedirs(book_dir, exist_ok=True)
    
    # 读取EPUB文件
    book = epub.read_epub(epub_path)
    
    # 收集处理结果
    result = {
        'book_name': book_name,
        'chapters': []
    }
    
    chunk_index = 1
    
    # 处理每个文档
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if not item.is_chapter():
            continue
            
        # 获取章节内容
        html_content = item.get_content().decode('utf-8')
        clean_text = clean_html_content(html_content)
        
        if not clean_text.strip():
            continue
            
        # 分割内容
        chunks = split_content(clean_text)
        
        chapter_info = {
            'title': item.get_name(),
            'chunks': []
        }
        
        # 保存每个块
        for i, chunk in enumerate(chunks, 1):
            chunk_data = {
                'content': chunk,
                'chunk_index': chunk_index,
                'chapter_chunk_index': i
            }
            
            # 保存到文件
            output_file = os.path.join(book_dir, f'chunk_{chunk_index:04d}.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
            
            chapter_info['chunks'].append(chunk_data)
            chunk_index += 1
        
        result['chapters'].append(chapter_info)
    
    # 保存处理信息
    info_file = os.path.join(book_dir, 'book_info.json')
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result 