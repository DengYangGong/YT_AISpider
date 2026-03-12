# YT_AISpider

**YT_AISpider** 是一个基于本地大语言模型（LLM）的 **YouTube 字幕下载与智能翻译工具**。

该工具可以自动抓取 YouTube 视频字幕，对字幕进行清洗与处理，并利用本地翻译模型进行高质量翻译，同时结合 **RAG（检索增强生成）术语系统**提升专业领域翻译准确度，最终生成双语字幕文件。

与依赖云 API 的方案不同，**YT_AISpider 完全本地运行**，适用于离线环境、大规模字幕翻译任务以及对数据隐私要求较高的场景。

------

# 项目特性

### 🎬 自动下载 YouTube 字幕

输入视频 URL，即可自动下载对应字幕（支持自动生成字幕）。

### 🧹 字幕自动清洗

对 YouTube 自动字幕进行处理，包括：

- 合并断句
- 清理重复/重叠字幕
- 按最大词数切分长句
- 重新分配时间戳

### 🤖 本地 LLM 翻译

使用本地翻译模型 **HY-MT1.5** 进行字幕翻译，无需调用任何在线 API。

### 📚 RAG 术语增强

通过向量数据库检索相关术语知识，将专业词汇注入提示词，显著提升翻译准确度。

### 🧠 短期上下文记忆

自动保留最近 3 句原文作为上下文，使翻译更连贯。

### 🌍 自动生成双语字幕

输出：

- 双语字幕（原文 + 译文）
- 纯中文字幕

### ⚡ 完全离线运行

整个流程 **无需网络 API**，适合本地部署。

---

* # 工作流程

  

  

  详细流程：

  1. 输入 YouTube 链接，下载字幕文件（SRT 格式）。
  2. 清洗字幕：解析 SRT，合并重叠片段，按最大词数（默认 23）切分长句，重新计算时间轴。
  3. 对每一条字幕：
     - 从向量数据库中检索最相关的 k 条术语知识（默认 k=3）。
     - 获取最近 3 句原文作为上下文。
     - 调用本地翻译模型，生成译文。
  4. 将所有译文与原文对齐，生成双语字幕和纯中文字幕文件。

  ------

  # 安装方法

  ## 1 克隆项目

  bash

  ```
  git clone https://github.com/DengYangGong/YT_AISpider.git
  cd YT_AISpider
  ```

  

  ## 2 安装依赖

  bash

  ```
  pip install -r requirements.txt
  ```

  

  主要依赖包括：

  text

  ```
  torch
  transformers
  sentence-transformers
  langchain-huggingface
  langchain-community
  faiss-cpu
  yt-dlp
  tqdm
  ```

  

  ------

  # 模型准备

  本项目需要两个本地模型：

  ### 1. 翻译模型

  下载 **HY-MT1.5 翻译模型**（如 `HY-MT1.5-1.8B`）并放入 `models/` 目录，例如：

  text

  ```
  models/
  └── HY-MT1.5-1.8B
  ```

  

  ### 2. 嵌入模型（用于 RAG 向量检索）

  下载 **all-MiniLM-L6-v2** 嵌入模型（或您选择的 SentenceTransformer 模型）并放入 `models/all-MiniLM-L6-v2` 目录：

  text

  ```
  models/
  └── all-MiniLM-L6-v2
  ```

  

  若未提前下载，程序首次运行时会自动从 HuggingFace 下载，但建议预先下载以支持离线使用。

  ------

  # 使用方法

  ## 命令行模式

  直接运行主程序：

  bash

  ```
  python main.py
  ```

  

  根据提示输入 YouTube 视频链接，程序将自动执行下载、清洗、翻译并输出字幕文件。

  ## WebUI 模式（可选）

  启动简易 Web 界面：

  bash

  ```
  python webui/app.py
  ```

  

  然后在浏览器中打开显示的地址，通过图形界面操作。

  ------

  # 输出结果

  翻译完成后会在 `data/subtitles/` 目录下生成两个字幕文件：

  - `xxx_bilingual.srt`（双语字幕，原文+译文）
  - `xxx_zh.srt`（仅中文字幕）

  示例（双语字幕）：

  text

  ```
  1
  00:00:00,000 --> 00:00:06,130
  everybody wanted the AT-AT from Star Wars
  每个人都想要《星球大战》中的 AT-AT 步行机。
  ```

  

  ------

  - # 项目结构

    text

    ```
    YT_AISpider
    │
    ├── main.py                         # 程序入口（命令行）
    │
    ├── config                          # 配置管理
    │   ├── settings.py
    │   └── model_config.py
    │
    ├── core                            # AI核心系统
    │   ├── agent.py                    # Agent控制器（整合记忆与翻译）
    │   ├── context.py                  # 会话上下文（短期记忆）
    │   │
    │   ├── memory                      # 记忆系统
    │   │   ├── base.py
    │   │   ├── short_term.py
    │   │   ├── long_term.py
    │   │   └── vector_store.py
    │   │
    │   └── reasoning                   # 推理链
    │       ├── translator_chain.py
    │       └── prompt_templates.py
    │
    ├── tools                           # Agent工具
    │   ├── youtube_downloader.py
    │   ├── subtitle_processor.py
    │   ├── subtitle_writer.py
    │   └── video_metadata.py
    │
    ├── rag                             # RAG系统
    │   ├── rag_engine.py               
    │   ├── embedding_model.py
    │   │
    │   └── knowledge_base              # 原始术语知识库
    │       ├── film_television_terms.txt
    │       └── xxx.txt
    │
    ├── models                          # 本地模型存放目录
    │   ├── HY-MT1.5-1.8B
    │   └── all-MiniLM-L6-v2
    │
    ├── pipelines                       # AI任务流程
    │   └── translation_pipeline.py     # 主翻译流水线
    │
    ├── webui                           # Web界面（可选）
    │   └── app.py
    │
    ├── data                            # 运行时数据
    │   ├── subtitles                   # 下载/生成的字幕文件
    │   ├── videos                      # 下载的视频文件（可选）
    │   └── vector_db                   # 向量数据库索引
    │       ├── long_term               # LongTermMemory 使用的索引
    │       │   ├── index.faiss
    │       │   └── index.pkl
    │       └── index.faiss             # RAGEngine 旧版索引（可忽略）
    │
    ├── requirements.txt
    └── README.md
    ```

    

    ------

    # RAG 术语系统

    ### 知识库文件

    所有原始术语文件均位于 `rag/knowledge_base/`，每行一条术语或定义。示例内容（`robotics_core.txt`）：

    text

    ```
    AT-AT = 帝国四足步行机
    Spur Gear = 直齿轮
    Servo Horn = 舵机摇臂
    PLA = PLA塑料
    ```

    

    ### 向量索引构建

    首次运行（或强制重建）时，程序会：

    1. 读取所有 `.txt` 文件，逐行提取文本。
    2. 使用嵌入模型将文本转换为向量。
    3. 构建 FAISS 索引并保存至 `data/vector_db/long_term/`。

    ### 检索增强翻译

    在翻译每句字幕时，系统会从该索引中检索最相似的 k 条术语，并将其作为提示词的一部分传递给翻译模型，从而确保专业词汇的准确翻译。

    ### 更新知识库

    如果修改或添加了知识库文件，需要**强制重建索引**才能使新内容生效。可以通过以下方式之一：

    - 删除 `data/vector_db/long_term/` 目录后重新运行程序。
    - 在 `AISpiderAgent` 初始化时设置 `rebuild=True`（需修改代码）。

    ------

    # 未来计划

    - WebUI 图形界面优化（支持上传自定义术语文件、选择模型等）。
    - 更智能的字幕断句（基于语义而非单纯词数）。
    - 支持更多翻译模型（如 MarianMT、NLLB 等）。
    - 多语言翻译（目前仅英译中）。

    ------

    # 贡献

    欢迎提交 Issue 或 Pull Request 来改进项目。

    如果你有新的功能想法或优化建议，也非常欢迎交流。

    ------

    # 开源协议

    本项目采用 **MIT License** 开源。

    ------

    # 致谢

    感谢以下开源项目：

    - HuggingFace Transformers
    - HY-MT 翻译模型
    - yt-dlp
    - LangChain
    - FAISS
    - 开源 AI 社区
