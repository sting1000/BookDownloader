#!/usr/bin/env python3
"""
电子书下载器 - 使用 macOS 原生对话框
"""

import subprocess
import urllib.request
import urllib.parse
import json
import os
import re
import sys

def run_applescript(script):
    """执行 AppleScript 并返回结果"""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def show_input_dialog(title, message, default=""):
    """显示输入对话框"""
    script = f'''
    tell application "System Events"
        activate
        set userInput to display dialog "{message}" default answer "{default}" with title "{title}" buttons {{"取消", "确定"}} default button "确定"
        return text returned of userInput
    end tell
    '''
    result, success = run_applescript(script)
    return result if success else None

def show_list_dialog(title, message, items):
    """显示列表选择对话框"""
    items_str = ', '.join([f'"{item}"' for item in items])
    script = f'''
    tell application "System Events"
        activate
        set selectedItem to choose from list {{{items_str}}} with title "{title}" with prompt "{message}" default items {{}}
        if selectedItem is false then
            return ""
        else
            return item 1 of selectedItem
        end if
    end tell
    '''
    result, success = run_applescript(script)
    return result if success and result else None

def show_progress_notification(title, message):
    """显示通知"""
    script = f'display notification "{message}" with title "{title}"'
    run_applescript(script)

def show_alert(title, message, is_error=False):
    """显示警告对话框"""
    icon = "stop" if is_error else "note"
    script = f'''
    tell application "System Events"
        activate
        display alert "{title}" message "{message}" as {"critical" if is_error else "informational"}
    end tell
    '''
    run_applescript(script)

def ask_yes_no(title, message):
    """询问是/否"""
    script = f'''
    tell application "System Events"
        activate
        set response to display dialog "{message}" with title "{title}" buttons {{"否", "是"}} default button "是"
        return button returned of response
    end tell
    '''
    result, success = run_applescript(script)
    return success and result == "是"

def choose_save_location(filename):
    """选择保存位置"""
    downloads = os.path.expanduser("~/Downloads")
    script = f'''
    tell application "System Events"
        activate
        set savePath to choose file name with prompt "保存电子书" default name "{filename}" default location POSIX file "{downloads}"
        return POSIX path of savePath
    end tell
    '''
    result, success = run_applescript(script)
    return result if success else None

def search_github(book_name):
    """在 GitHub 上搜索 epub 文件"""
    query = urllib.parse.quote(f"{book_name} extension:epub")
    url = f"https://api.github.com/search/code?q={query}&per_page=10"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BookDownloader/1.0"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('items', [])
    except Exception as e:
        show_alert("搜索失败", str(e), is_error=True)
        return []

def download_file(url, filepath):
    """下载文件"""
    headers = {"User-Agent": "BookDownloader/1.0"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        show_progress_notification("下载中", f"正在下载: {os.path.basename(filepath)}")
        
        with urllib.request.urlopen(req, timeout=120) as response:
            data = response.read()
            
            with open(filepath, 'wb') as f:
                f.write(data)
        
        return True
    except Exception as e:
        show_alert("下载失败", str(e), is_error=True)
        return False

def sanitize_filename(name):
    """清理文件名"""
    return re.sub(r'[<>:"/\\|?*]', '', name)

def main():
    # 获取书名
    book_name = show_input_dialog("📚 电子书下载器", "请输入要搜索的书名:")
    
    if not book_name:
        sys.exit(0)
    
    show_progress_notification("搜索中", f"正在搜索: {book_name}")
    
    # 搜索
    results = search_github(book_name)
    
    if not results:
        show_alert("未找到", "未找到相关电子书，请尝试其他书名或关键词")
        # 重新开始
        main()
        return
    
    # 显示结果列表
    items = []
    for item in results:
        name = item['name']
        repo = item['repository']['full_name'].split('/')[-1]
        display = f"{name} ({repo})"
        # AppleScript 列表项长度限制，截断
        if len(display) > 60:
            display = display[:57] + "..."
        items.append(display)
    
    selected = show_list_dialog(
        "搜索结果",
        f"找到 {len(results)} 本电子书，请选择:",
        items
    )
    
    if not selected:
        sys.exit(0)
    
    # 找到选中的索引
    idx = items.index(selected)
    item = results[idx]
    
    # 获取下载链接
    repo = item['repository']['full_name']
    path = item['path']
    download_url = f"https://github.com/{repo}/raw/HEAD/{urllib.parse.quote(path)}"
    
    filename = sanitize_filename(item['name'])
    
    # 选择保存位置
    save_path = choose_save_location(filename)
    
    if not save_path:
        sys.exit(0)
    
    # 确保扩展名
    if not save_path.endswith('.epub'):
        save_path += '.epub'
    
    # 下载
    if download_file(download_url, save_path):
        if ask_yes_no("下载完成", f"已保存到:\n{save_path}\n\n是否立即打开?"):
            subprocess.run(['open', save_path])
        
        # 询问是否继续搜索
        if ask_yes_no("继续", "是否继续搜索其他书籍?"):
            main()

if __name__ == "__main__":
    main()
