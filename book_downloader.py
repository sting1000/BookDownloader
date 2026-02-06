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

def create_progress_html(book_name):
    """创建进度显示 HTML 文件"""
    html_path = '/tmp/book_search_progress.html'
    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="1">
    <title>搜索中 - {book_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
               padding: 40px; text-align: center; background: #f5f5f7; }}
        .container {{ background: white; padding: 30px; border-radius: 12px; 
                     box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }}
        h2 {{ color: #333; margin-bottom: 20px; }}
        .progress-bar {{ background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden; }}
        .progress-fill {{ background: linear-gradient(90deg, #007aff, #5856d6); height: 100%; 
                         transition: width 0.3s; }}
        .status {{ margin-top: 15px; color: #666; }}
        .repo {{ font-size: 14px; color: #999; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🔍 正在搜索: {book_name}</h2>
        <div class="progress-bar"><div class="progress-fill" style="width: 0%"></div></div>
        <div class="status">准备中...</div>
        <div class="repo"></div>
    </div>
</body>
</html>
'''
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return html_path

def update_progress_html(current, total, repo_name, found_count):
    """更新进度 HTML"""
    html_path = '/tmp/book_search_progress.html'
    progress = int((current / total) * 100)
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新进度条
        content = content.replace(
            'style="width: 0%"', f'style="width: {progress}%"'
        ).replace(
            f'style="width: {progress-int(100/total)}%"', f'style="width: {progress}%"'
        )
        
        # 更新状态文字
        import re
        content = re.sub(
            r'<div class="status">.*?</div>',
            f'<div class="status">进度: {current}/{total} ({progress}%) - 已找到 {found_count} 本</div>',
            content
        )
        content = re.sub(
            r'<div class="repo">.*?</div>',
            f'<div class="repo">正在扫描: {repo_name}</div>',
            content
        )
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except:
        pass

def show_progress_window(title, book_name, repo_list, search_func):
    """显示搜索进度并执行搜索"""
    total = len(repo_list)
    all_results = []
    
    # 创建并打开进度页面
    html_path = create_progress_html(book_name)
    browser_proc = subprocess.Popen(
        ['open', '-a', 'Safari', html_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    import time
    time.sleep(0.5)  # 等待浏览器打开
    
    for i, repo in enumerate(repo_list):
        # 更新进度
        update_progress_html(i + 1, total, repo.split('/')[-1], len(all_results))
        
        # 执行搜索
        results = search_func(repo, book_name)
        all_results.extend(results)
        
        # 如果找到足够多结果，提前结束
        if len(all_results) >= 20:
            break
    
    # 关闭进度页面
    subprocess.run(['osascript', '-e', '''
        tell application "Safari"
            close (every tab of every window whose URL contains "book_search_progress")
        end tell
    '''], capture_output=True)
    
    return all_results

def search_github(book_name):
    """在 GitHub 上搜索 epub 文件，显示 UI 进度"""
    # 使用进度窗口搜索
    all_results = show_progress_window(
        f"搜索: {book_name}",
        book_name,
        KNOWN_EBOOK_REPOS,
        search_repo_for_epub
    )
    
    # 如果找到了就返回
    if all_results:
        return all_results[:20]
    
    # 尝试使用 gh CLI 搜索
    try:
        show_progress_notification("搜索中", "正在使用 GitHub API 搜索...")
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
    
    return []

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
    book_name = show_input_dialog("📚 电子书下载器", "请输入要搜索的书名:")
    
    if not book_name:
        sys.exit(0)
    
    # 搜索（会显示进度窗口）
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
