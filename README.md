# 规范繁体转换

基于 Streamlit 和 OpenCC 的中文文本、TXT、Markdown、Word 简繁转换工具。默认使用 TerryTian-tech 的“简体→规范繁体”方案，支持繁体字形规范化及 OpenCC 的其他转换方向。

## 词库来源

- [TerryTian-tech / OpenCC 规范繁体](https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards)
- 固定版本：`bb61139b5f783e7767a4fc4865591b805b942dc3`，Apache-2.0。
- 原始配置、词库、授权及设计说明保存在 `vendor/tonggui/`，文件校验值见 `SOURCE.json`。上游文件保持原样，界面与文档转换由本项目提供。
- `s2gov` 直接加载上游 `s2t.json`，`t2gov` 加载上游 `t2gov.json`；使用官方 `OpenCC==1.3.2`，包括相容汉字正规化与词组优先匹配。

“规范繁体”按该社区项目的方案转换；上游对部分字形作了调整，不等同于官方字表的逐项复刻。出版前仍需校对。旧版按投稿 Word 文档整理的 73 条规则及用语替换已移除。

## 使用

选择转换方案，输入文字或上传 `.txt`、`.md`、`.docx` 文件。Word 正文、表格、页眉页脚、脚注、尾注均转换，保留原有文字格式。自定义 JSON 词典在 OpenCC 转换之前执行。

“字表与词库下载”提供《通用规范汉字表》（2013）官方 PDF 链接、单个 TXT 字表/词库，以及包含全部配套配置和授权的 ZIP。官方 PDF 为外部资源；转换词库随应用打包，转换时无需连接上游仓库。

## 本地运行

推荐 Python 3.12，新建独立环境，不使用旧仓库提交的 `venv`。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud

1. 将本项目推送至 GitHub。
2. 在 Streamlit Community Cloud 选择仓库 `alzco/Chinese-T-S-DocConverter`、分支 `main`、入口 `app.py`。
3. Advanced settings 中选择 Python 3.12，部署。已有应用在关联分支更新后自动重新构建。

Cloud 从 `requirements.txt` 安装官方 OpenCC，无需调用桌面程序、系统包管理器或运行时下载词库。勿同时安装 `opencc-python-reimplemented`，两者使用同一个 Python 模块名。

原在线地址：[chinese-t-s-docconverter.streamlit.app](https://chinese-t-s-docconverter.streamlit.app/)。本 README 不代表此地址已更新；以上线检查为准。

## 测试

```sh
python -B -m unittest discover -s tests -v
```

覆盖上游文件校验、配置加载、相容汉字正规化、语义词组、Word 格式与脚注尾注、下载包完整性及 Streamlit 交互。
