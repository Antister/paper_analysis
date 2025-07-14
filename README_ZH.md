# 📊 Paper Analysis

本项目是一个简单的 DBLP 学术数据分析工具。它从 [DBLP](dblp.org) 数据库中爬取指定顶级计算机科学会议论文数据，并进行一系列分析，包括：

  * **论文数量统计与可视化**：统计每届会议的论文数量，并绘制成折线图，以展示其变化趋势。
  * **研究热点分析**：基于论文标题提取关键词，并生成词云图，以分析历史研究热点。
  * **论文数量预测**：基于历年数据，对下一届会议可能发表的论文数量进行预测。

## 🚀 特点

  * **并行数据处理**：在数据验证、解析和词云图生成等环节采用并行处理，以提升数据处理效率。
  * **模块化设计**：项目代码结构清晰，功能模块化，易于扩展和维护。
  * **C++ 扩展**：使用 C++ 编写核心的计算密集型任务（如词频统计），并通过 `nanobind` 绑定到 Python，以提升性能。
  * **自动化构建**：使用 CMake 和 Ninja 自动化构建 C++ 扩展模块，简化开发流程。

## ⚙️ 安装与使用

### 环境要求

  * [uv](https://github.com/astral-sh/uv)
  * 支持 C++23 的编译器

本项目依赖的 Python 包已在 `pyproject.toml` 文件中列出，主要包括：

  * `beautifulsoup4`
  * `lxml`
  * `matplotlib`
  * `nanobind`
  * `numpy`
  * `scikit-learn`
  * `wordcloud`

### 运行项目

1.  **克隆项目**

    ```bash
    git clone https://github.com/Antister/paper_analysis
    cd paper-analysis
    ```

2.  **直接运行**

    ```bash
    uv run Entry.py
    ```

使用uv直接运行 `Entry.py` 即可启动项目。首次运行时，项目会自动安装依赖以及从 DBLP 数据库下载所需的数据文件，并编译 C++ 扩展模块。

程序会执行以下操作：

1.  **构建 C++ 扩展**：编译 `check.cpp` 和 `freq.cpp`，生成 Python 可调用的模块。
2.  **数据获取**：
      * 从 DBLP 下载 `dblp.xml.gz` 并解压，同时下载相应的 DTD 和 MD5 校验文件以确保数据完整性。
      * 爬取指定会议（默认为 AAAI, CVPR, ICSE）在 2020 年至 2024 年间的 HTML 页面数据。
3.  **数据解析与验证**：
      * 解析 XML 和 HTML 文件，提取论文信息。
      * 将 HTML 数据与 XML 数据进行交叉验证，以确保数据一致性。
4.  **数据分析与可视化**：
      * 统计并绘制各会议的年度论文数量变化趋势图，并保存到 `out/` 目录。
      * 提取论文标题中的关键词，生成每年的词云图，并保存到 `out/` 目录。
5.  **论文数量预测**：使用线性回归模型，预测下一年度各会议的论文数量。

## 📦 项目结构

```
paper-analysis/
├── src/
│   ├── cpp/                 # C++ 核心模块
│   │   ├── check.cpp        # 数据验证模块
│   │   ├── freq.cpp         # 词频统计模块
│   │   ├── paper.hpp        # 论文数据结构定义
│   │   └── words.hpp        # 停用词和术语表
│   └── python/              # Python 主要逻辑
│       ├── analyse.py       # 数据分析
│       ├── fetch.py         # 数据获取
│       ├── main.py          # 主程序
│       ├── parse.py         # 数据解析
│       └── predict.py       # 论文数量预测
├── Entry.py                 # 项目入口文件
├── pyproject.toml           # 项目配置文件
└── README.md                # 项目文档
```

## 📄 许可证

本项目采用 GPLv3 许可证。详情请参阅 `LICENSE` 文件。