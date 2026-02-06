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
    """在 GitHub 上搜索 epub 文件，使用 gh CLI 认证"""
    query = f"{book_name} extension:epub"
    
    try:
        # 使用 gh CLI 进行认证搜索
        result = subprocess.run(
            ['gh', 'api', 'search/code', '-X', 'GET', 
             '-f', f'q={query}', '-f', 'per_page=10'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            # 如果 gh 失败，尝试使用仓库搜索（不需要认证）
            return search_github_repos(book_name)
        
        data = json.loads(result.stdout)
        return data.get('items', [])
    except FileNotFoundError:
        # gh CLI 未安装，使用备用方案
        return search_github_repos(book_name)
    except Exception as e:
        show_alert("搜索失败", str(e), is_error=True)
        return []

def search_github_repos(book_name):
    """备用方案：搜索仓库中的 epub 文件"""
    # 搜索包含电子书的知名仓库
    known_repos = [
        "https://api.github.com/repos/iamseancheney/python_for_data_analysis_2nd_chinese_version/contents",
    ]
    
    # 使用仓库搜索 API（不需要认证）
    query = urllib.parse.quote(f"{book_name} epub in:path")
    url = f"https://api.github.com/search/repositories?q={query}&per_page=5"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BookDownloader/1.0"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            repos = data.get('items', [])
            
            # 在找到的仓库中搜索 epub 文件
            results = []
            for repo in repos[:3]:  # 只检查前3个仓库
                epub_files = search_repo_for_epub(repo['full_name'], book_name)
                results.extend(epub_files)
                if len(results) >= 10:
                    break
            
            return results
    except Exception as e:
        show_alert("搜索失败", str(e), is_error=True)
        return []

def search_repo_for_epub(repo_name, book_name):
    """在指定仓库中搜索 epub 文件"""
    url = f"https://api.github.com/repos/{repo_name}/git/trees/HEAD?recursive=1"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BookDownloader/1.0"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            tree = data.get('tree', [])
            
            results = []
            book_name_lower = book_name.lower()
            
            for item in tree:
                path = item.get('path', '')
                if path.endswith('.epub'):
                    filename = os.path.basename(path)
                    # 检查文件名是否匹配搜索词
                    if book_name_lower in filename.lower() or book_name_lower in path.lower():
                        results.append({
                            'name': filename,
                            'path': path,
                            'repository': {'full_name': repo_name}
                        })
            
            return results
    except:
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
