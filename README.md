# 📚 电子书下载器 (BookDownloader)

一个简单的 macOS 应用，用于搜索和下载 EPUB 电子书。双击即用，输入书名即可搜索下载。

## ✨ 功能特性

- 🔍 **智能搜索** - 支持中英文书名搜索
- 📚 **多源扫描** - 自动扫描 15+ 个 GitHub 电子书仓库
- 📊 **实时进度** - Safari 窗口显示搜索进度条
- 📥 **一键下载** - 选择保存位置后自动下载
- 📖 **快速阅读** - 下载完成后可直接用 Apple Books 打开
- 🎨 **原生体验** - 使用 macOS 原生对话框

## 📷 截图

### 搜索界面
```
┌───────────────────────────────┐
│   📚 电子书下载器          │
├───────────────────────────────┤
│  请输入要搜索的书名:       │
│  ┌───────────────────────┐   │
│  │ Python              │   │
│  └───────────────────────┘   │
│         [取消] [确定]       │
└───────────────────────────────┘
```

### 搜索进度
```
┌───────────────────────────────┐
│  🔍 正在搜索: Python        │
│                               │
│  ██████████░░░░░░░░░░  53%   │
│                               │
│  进度: 8/15 - 已找到 12 本      │
│  正在扫描: CS-Books           │
└───────────────────────────────┘
```

## 🚀 安装

### 方法一：直接下载

```bash
# 克隆项目
git clone https://github.com/sting1000/BookDownloader.git

# 进入目录
cd BookDownloader

# 双击打开应用
open BookDownloader.app
```

### 方法二：命令行运行

```bash
python3 book_downloader.py
```

> ⚠️ **首次打开**: 由于应用未签名，需要右键点击 app → 打开 → 确认打开

## 📖 使用方法

1. **启动应用** - 双击 `BookDownloader.app` 或运行 `python3 book_downloader.py`
2. **输入书名** - 在弹出的对话框中输入想搜索的书名（支持中英文）
3. **等待搜索** - Safari 会打开一个进度页面，实时显示搜索进度
4. **选择书籍** - 从搜索结果列表中选择想要的书
5. **保存文件** - 选择保存位置（默认为 Downloads 文件夹）
6. **开始阅读** - 下载完成后可选择立即用 Apple Books 打开

## 📁 搜索源

本工具会自动扫描以下 GitHub 电子书仓库：

| 仓库 | 说明 |
|------|------|
| fancy88/iBook | 中文电子书合集 |
| threerocks/studyFiles | 学习资料 |
| hehonghui/awesome-english-ebooks | 英文电子书 |
| forthespada/CS-Books | 计算机书籍 |
| imarvinle/awesome-cs-books | CS 经典书籍 |
| Tyson0314/java-books | Java 书籍 |
| justjavac/free-programming-books-zh_CN | 免费编程书籍 |
| programthink/books | 电子书库 |
| ... | 还有更多 |

## 🛠 系统要求

- **操作系统**: macOS 10.13 (High Sierra) 或更高版本
- **Python**: 3.6+（macOS 系统自带）
- **浏览器**: Safari（用于显示搜索进度）

## 📂 项目结构

```
BookDownloader/
├── BookDownloader.app/     # macOS 应用包
│   └── Contents/
│       ├── Info.plist
│       ├── MacOS/
│       │   ├── BookDownloader  # 启动脚本
│       │   └── book_downloader.py
│       └── Resources/
│           └── AppIcon.icns
├── book_downloader.py      # 主程序
├── README.md
└── .gitignore
```

## ❓ 常见问题

**Q: 搜索不到某本书？**
> 尝试使用更简短的关键词，如搜索“查理”而不是“穷查理宝典”

**Q: 应用无法打开？**
> 右键点击 app → 打开 → 确认打开（首次运行需要）

**Q: 搜索速度慢？**
> 这是因为需要扫描多个仓库，请耐心等待。如果已找到足够结果会自动停止

## ⚠️ 免责声明

- 本工具仅搜索 GitHub 上公开分享的电子书资源
- 请尊重版权，仅下载合法分享的书籍
- 如果喜欢某本书，请支持正版购买
- 开发者不对下载内容的合法性负责

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

Made with ❤️ by [sting1000](https://github.com/sting1000)
