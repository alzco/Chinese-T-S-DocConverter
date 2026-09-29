# 规范汉字繁简转换工具

基于 OpenCC 与《通用规范汉字表》的中文简繁转换工具，支持自定义词典功能。采用 Streamlit 网页界面，默认将简体转换为规范繁体，并统一混合输入中已有的繁体、异体字形。

## 功能

- **文档转换**：默认打开，支持 TXT、Markdown 和 Word（`.docx`）。Word 正文、表格、页眉页脚、脚注和尾注均参与转换，保留原有文字格式。
- **文本转换**：输入、预览并下载结果，也可加载示例或清空内容。
- **方向选择**：源语言和目标语言分开选择，支持简体、规范繁体、台湾繁体和香港繁体的可用转换方向；两端不能相同。
- **自定义词典**：新增、删除映射，导入和导出 JSON 词典。
- **字表与词库下载**：提供官方字表 PDF 链接、单个词库及完整词库 ZIP。

## 词库来源

- [TerryTian-tech / OpenCC 规范繁体](https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards)
- 固定版本：`bb61139b5f783e7767a4fc4865591b805b942dc3`，Apache-2.0。
- 原始配置、词库、授权及设计说明保存在 `vendor/tonggui/`，文件校验值见 `SOURCE.json`。上游文件保持原样，界面与文档转换由本项目提供。
- `s2gov` 依次执行上游 `s2t.json` 和 `t2gov.json`，兼顾简转繁及混合输入中已有繁体、异体字的规范化；`t2gov` 加载上游 `t2gov.json`。使用官方 `OpenCC==1.3.2`，包括相容汉字正规化与词组优先匹配。

“规范繁体”按该社区项目的方案转换；上游对部分字形作了调整，不等同于官方字表的逐项复刻。出版前仍需校对。旧版按投稿 Word 文档整理的 73 条规则及用语替换已移除。

## 使用

1. 选择源语言和目标语言，默认“简体→规范繁体”。中间的 **⇄** 按钮可对调方向；“其他繁体”用于来源不明确的繁体输入，不能作为目标，因此该来源下对调按钮不可用。
2. 在“文档转换”上传文件，或切换到“文本转换”输入内容。
3. 点击转换，检查结果后下载。更换方向后，需重新转换。

默认方案会先简转繁，再执行繁体字形规范化。例如 `两、侷限、羣、批註、悅` 转为 `兩、局限、群、批注、悦`。具体字词遵循上游词库及词组匹配，不应把示例中的字形变化理解为所有语境下的统一替换。

自定义 JSON 词典在 OpenCC 转换**之前**执行，替换后的文字仍会经过所选转换方案。例如：

```json
{
  "计算机": "信息处理设备"
}
```

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

1. 登录 Streamlit Community Cloud，新建应用并连接本 GitHub 仓库。
2. 选择仓库 `alzco/Chinese-T-S-DocConverter`、分支 `main`、入口 `app.py`。
3. Advanced settings 中选择 Python 3.12，部署。已有应用在关联分支更新后自动重新构建。

Cloud 从 `requirements.txt` 安装官方 OpenCC，无需调用桌面程序、系统包管理器或运行时下载词库。勿同时安装 `opencc-python-reimplemented`，两者使用同一个 Python 模块名。

原在线地址：[chinese-t-s-docconverter.streamlit.app](https://chinese-t-s-docconverter.streamlit.app/)。本 README 不代表此地址已更新；以上线检查为准。

## 测试

```sh
python -B -m unittest discover -s tests -v
```

覆盖上游文件校验、配置加载、相容汉字正规化、混合简繁输入、语义词组、Word 格式与脚注尾注、下载包完整性，以及语言对调、选项联动等 Streamlit 交互。
