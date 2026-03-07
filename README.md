# YT_AISpider

**YT_AISpider** 是一个基于本地大语言模型（LLM）的 **YouTube 字幕下载与智能翻译工具**。

该工具可以自动抓取 YouTube 视频字幕，对字幕进行清洗与处理，并利用本地翻译模型进行高质量翻译，同时结合 **RAG（检索增强生成）术语系统**提升专业领域翻译准确度，最终生成双语字幕文件。

与依赖云 API 的方案不同，**YT_AISpider 完全本地运行**，适用于离线环境、大规模字幕翻译任务以及对数据隐私要求较高的场景。

---

# 项目特性

### 🎬 自动下载 YouTube 字幕

输入视频 URL，即可自动下载对应字幕。

### 🧹 字幕自动清洗

对 YouTube 自动字幕进行处理，包括：

* 合并断句
* 清理重复字幕
* 优化字幕结构

### 🤖 本地 LLM 翻译

使用本地翻译模型 **HY-MT1.5** 进行字幕翻译，无需调用任何在线 API。

### 📚 RAG 术语增强

通过术语知识库（knowledge base）提高翻译准确度，避免专业词汇翻译错误。

### 🌍 自动生成双语字幕

输出：

* 双语字幕
* 中文字幕

### ⚡ 完全离线运行

整个流程 **无需网络 API**，适合本地部署。

---

# 工作流程

```id="pipeline_cn"
YouTube 视频链接
        │
        ▼
字幕下载
        │
        ▼
字幕清洗
        │
        ▼
RAG术语检索
        │
        ▼
LLM字幕翻译
        │
        ▼
生成双语字幕
```

---

# 安装方法

## 1 克隆项目

```bash
git clone https://github.com/DengYangGong/YT_AISpider.git
cd YT_AISpider
```

---

## 2 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：

```
torch
transformers
tqdm
sentence-transformers
faiss-cpu
yt-dlp
```

---

# 模型准备

下载 **HY-MT1.5 翻译模型** 并放入 `model` 目录，例如：

```
model/
└── HY-MT1.5-1.8B
```

程序启动时会自动加载该模型。

---

# 使用方法

运行主程序：

```bash
python main.py
```

程序会提示输入 YouTube 视频地址：

```
视频网址：
```

输入视频链接后，程序会自动执行以下流程：

1. 下载字幕
2. 清洗字幕
3. 调用本地模型翻译
4. 输出字幕文件

---

# 输出结果

翻译完成后会生成两个字幕文件：

```
xxx_bilingual.srt
xxx_zh.srt
```

示例：

```
1
00:00:00,000 --> 00:00:06,130
everybody wanted the AT-AT from Star Wars
每个人都想要《星球大战》中的 AT-AT 步行机。
```

---

# 项目结构

```
YT_AISpider
│
├── main.py                 # 程序入口
│
├── video_downloader.py     # YouTube字幕下载
├── subtitle_processor.py   # 字幕清洗处理
├── subtitle_translator.py  # LLM翻译模块
├── rag_engine.py           # RAG术语检索模块
│
├── knowledge_base          # 术语知识库
│   ├── terms.txt
│   └── robotics.txt
│
├── subtitle                # 下载的字幕文件
│
├── model                   # 本地翻译模型
│
├── requirements.txt
└── README.md
```

---

# RAG术语系统

项目支持通过知识库增强翻译效果。

术语库示例：

```
AT-AT = 帝国四足步行机
Spur Gear = 直齿轮
Servo Horn = 舵机摇臂
PLA = PLA塑料
```

翻译时模型会参考这些术语，从而提高专业词汇的翻译准确性。

---

# 使用示例

输入：

```
https://www.youtube.com/watch?v=xxxx
```

执行流程：

```
下载字幕 → 清洗字幕 → LLM翻译 → 生成字幕
```

输出：

```
video_bilingual.srt
video_zh.srt
```

---

# 未来计划

计划继续完善以下功能：

* WebUI 图形界面
* 翻译缓存机制
* 批量字幕翻译
* 更智能的字幕断句
* 更高效的术语检索
* 支持多语言翻译

---

# 贡献

欢迎提交 Issue 或 Pull Request 来改进项目。

如果你有新的功能想法或优化建议，也非常欢迎交流。

---

# 开源协议

本项目采用 **MIT License** 开源。

---

# 致谢

感谢以下开源项目：

* HuggingFace Transformers
* HY-MT 翻译模型
* yt-dlp
* 开源 AI 社区
