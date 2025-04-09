# OpenCC 繁简转换工具

基于 [OpenCC](https://github.com/BYVoid/OpenCC) 的中文简繁转换工具，支持自定义词典功能。

## 功能特点

- 支持多种转换方向（简体、繁体、台湾繁体、香港繁体、日文新字体）
- 支持自定义词典，可以添加、保存和加载自定义转换规则
- 简洁直观的用户界面
- 基于 Streamlit 开发，易于部署和使用

## 在线使用


## 本地安装说明

1. 确保已安装 Python 3.7 或更高版本
2. 克隆或下载本项目
3. 创建并激活虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

4. 安装依赖

```bash
pip install -r requirements.txt
```

## 本地使用方法

1. 启动应用

```bash
streamlit run app.py
```

2. 在浏览器中访问应用（通常是 http://localhost:8501）

3. 使用界面：
   - 在左侧输入框中输入要转换的文本
   - 在侧边栏选择转换方向
   - 点击"转换"按钮进行转换
   - 转换结果将显示在右侧输出框中

4. 自定义词典：
   - 在侧边栏的"自定义词典"部分添加新词条
   - 可以保存词典到文件或从文件加载词典
   - 可以删除不需要的词条

## 支持的转换方向

- s2t: 简体 → 繁体
- t2s: 繁体 → 简体
- s2tw: 简体 → 台湾繁体
- tw2s: 台湾繁体 → 简体
- s2hk: 简体 → 香港繁体
- hk2s: 香港繁体 → 简体
- s2twp: 简体 → 台湾繁体（台湾用词）
- tw2sp: 台湾繁体 → 简体（大陆用词）
- t2tw: 繁体 → 台湾繁体
- hk2t: 香港繁体 → 繁体
- t2hk: 繁体 → 香港繁体
- t2jp: 繁体 → 日文新字体
- jp2t: 日文新字体 → 繁体
- tw2t: 台湾繁体 → 繁体

## 自定义词典格式

自定义词典以 JSON 格式存储，格式如下：

```json
{
  "源词汇1": "目标词汇1",
  "源词汇2": "目标词汇2",
  ...
}
```

例如：

```json
{
  "计算机": "電腦",
  "软件": "軟體"
}
```

## 核心文件说明

- `app.py`: Streamlit 应用主文件
- `opencc_converter.py`: OpenCC 转换核心功能
- `requirements.txt`: 项目依赖
- `custom_dict.json`: 默认的自定义词典文件（如果存在）

## 许可证

本项目基于 MIT 许可证开源。

## 致谢

- [OpenCC](https://github.com/BYVoid/OpenCC): 开源中文繁简转换工具
- [Streamlit](https://streamlit.io/): 用于构建应用的框架
