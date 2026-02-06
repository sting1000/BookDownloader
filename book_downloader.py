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

# 已知的电子书仓库列表
KNOWN_EBOOK_REPOS = [
    "fancy88/iBook",
    "threerocks/studyFiles",
    "gedoor/legado",
    "hehonghui/awesome-english-ebooks",
    "itdevbooks/pdf",
    "forthespada/CS-Books",
    "imarvinle/awesome-cs-books",
    "Tyson0314/java-books",
    "justjavac/free-programming-books-zh_CN",
    "EbookFoundation/free-programming-books",
    "programthink/books",
    "royeo/awesome-programming-books",
    "XiangLinPro/IT_book",
    "tangtangcoding/C-C-",
    "woai3c/recommended-books",
]

def show_searching_dialog():
    """显示搜索中的对话框"""
    script = '''
    tell application "System Events"
        activate
        display dialog "🔍 正在搜索中...

正在扫描多个电子书仓库，请稍候..." with title "搜索中" buttons {"取消"} giving up after 1 with icon note
    end tell
    '''
    # 异步显示，不等待结果
    subprocess.Popen(['osascript', '-e', script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def close_dialog():
    """关闭对话框"""
    script = '''
    tell application "System Events"
        try
            click button "取消" of window 1
        end try
    end tell
    '''
    subprocess.run(['osascript', '-e', script], capture_output=True)

def search_github(book_name, progress_callback=None):
    """在 GitHub 上搜索 epub 文件"""
    all_results = []
    total_repos = len(KNOWN_EBOOK_REPOS)
    
    # 1. 首先在已知的电子书仓库中搜索
    for i, repo in enumerate(KNOWN_EBOOK_REPOS):
        # 显示进度通知
        show_progress_notification("搜索中", f"正在扫描: {repo.split('/')[-1]} ({i+1}/{total_repos})")
        
        results = search_repo_for_epub(repo, book_name)
        all_results.extend(results)
        if len(all_results) >= 20:
            break
    
    # 2. 如果找到了就返回
    if all_results:
        return all_results[:15]
    
    # 3. 尝试使用 gh CLI 搜索
    try:
        query = f"{book_name} extension:epub"
        result = subprocess.run(
            ['gh', 'api', 'search/code', '-X', 'GET', 
             '-f', f'q={query}', '-f', 'per_page=10'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            items = data.get('items', [])
            if items:
                return items
    except:
        pass
    
    # 4. 备用：搜索仓库名
    return search_github_repos(book_name)

def search_github_repos(book_name):
    """搜索包含关键词的仓库"""
    query = urllib.parse.quote(f"{book_name} epub")
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
            # 分割搜索词以支持多关键词搜索
            keywords = [k.strip() for k in book_name.replace('，', ' ').replace(',', ' ').split() if k.strip()]
            
            for item in tree:
                path = item.get('path', '')
                if path.endswith('.epub'):
                    filename = os.path.basename(path)
                    # 检查文件名是否包含任一关键词（中文直接比较，英文忽略大小写）
                    path_lower = path.lower()
                    filename_lower = filename.lower()
                    
                    for keyword in keywords:
                        kw_lower = keyword.lower()
                        if keyword in path or keyword in filename or kw_lower in path_lower or kw_lower in filename_lower:
                            results.append({
                                'name': filename,
                                'path': path,
                                'repository': {'full_name': repo_name}
                            })
                            break
            
            return results
    except Exception as e:
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
    book_name = show_input_dialog("📚 电子书下载器", "请输入要搜索的书名（支持中英文）:")
    
    if not book_name:
        sys.exit(0)
    
    # 显示搜索开始提示
    show_alert("🔍 开始搜索", f"正在搜索: {book_name}\n\n将扫描 {len(KNOWN_EBOOK_REPOS)} 个电子书仓库，请查看通知中心了解进度...")
    
    # 搜索
    results = search_github(book_name)
    
    if not results:
        if ask_yes_no("未找到", "未找到相关电子书\n\n建议：\n• 尝试更简短的关键词\n• 使用书名中的核心词\n\n是否重新搜索？"):
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
