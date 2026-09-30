# 规范汉字繁简转换工具

基于 OpenCC 与《通用规范汉字表》的中文简繁转换工具，支持自定义词典、云端公共词典功能。采用 Streamlit 网页界面，默认将简体转换为规范繁体，并统一混合输入中已有的繁体、异体字形。

## 功能

- **文档转换**：默认打开，支持 TXT、Markdown 和 Word（`.docx`）。Word 正文、表格、页眉页脚、脚注和尾注均参与转换，保留原有文字格式。
- **文本转换**：输入、预览并复制结果，也可加载示例或清空内容。
- **方向选择**：源语言和目标语言分开选择，支持简体、规范繁体、台湾繁体和香港繁体的可用转换方向；两端不能相同。
- **自定义本地词典**：新增、删除映射，导入和导出 JSON 词典。
- **公共词典**：可新建公共词典，也可把词条合并到现有词典；其他用户可按需勾选，仅用于“简体 → 规范繁体”，默认不启用。
- **字表与词库下载**：提供官方字表 PDF 链接、单个词库及完整词库 ZIP。

## 在线使用

托管在Streamlit平台，在线地址：[chinese-t-s-docconverter.streamlit.app](https://chinese-t-s-docconverter.streamlit.app/)。

**提示：在线地址若12小时未使用会进入休眠，需要唤醒并等待 app启动。** 

除了在线使用之外，亦可本地部署运行。直接将该项目地址发送给AI部署。

## 词库来源

- [TerryTian-tech / OpenCC 规范繁体](https://github.com/TerryTian-tech/OpenCC-Traditional-Chinese-characters-according-to-Chinese-government-standards)
- 固定版本：`bb61139b5f783e7767a4fc4865591b805b942dc3`，Apache-2.0。
- 原始配置、词库、授权及设计说明保存在 `vendor/tonggui/`，文件校验值见 `SOURCE.json`。上游文件保持原样，界面与文档转换由本项目提供。
- `s2gov` 依次执行上游 `s2t.json` 和 `t2gov.json`，兼顾简转繁及混合输入中已有繁体、异体字的规范化；`t2gov` 加载上游 `t2gov.json`。使用官方 `OpenCC==1.3.2`，包括相容汉字正规化与词组优先匹配。

“规范繁体”按该社区项目的方案转换；上游对部分字形作了调整，不等同于官方字表的逐项复刻。出版前仍需校对。

## 使用方式

1. 选择源语言和目标语言，默认“简体→规范繁体”。中间的 **⇄** 按钮可对调方向；“其他繁体”用于来源不明确的繁体输入，不能作为目标，因此该来源下对调按钮不可用。
2. 在“文档转换”上传文件，或切换到“文本转换”输入内容。
3. 点击转换，检查结果后下载。更换方向后，需重新转换。

默认方案会先简转繁，再执行繁体字形规范化。例如 `两、侷限、羣、批註、悅` 转为 `兩、局限、群、批注、悦`。具体字词遵循上游词库及词组匹配。

## 自定义词典

自定义 JSON 词典命中的替换词会作为最终结果保留，不再被 OpenCC 改写。优先级固定为：**自定义本地词典 ＞ 云端公共词典 ＞ OpenCC**。页面可展开已有词条，多选后批量删除，也可导入或导出 JSON。格式例如：

```json
{
  "钱钟书": "錢鍾書"
}
```

网页刷新后，自定义词典缓存将删除，有需要的话请及时下载。优质词典建议上传到云端公共词典，以便下次直接选用。

## 公共词典（Supabase）

个人词典默认只保留在当前会话。页面提供独立且默认展开的“上传到公共词典”入口：选择 JSON 文件，填写名称、查看词条，勾选同意公开，再点击始终可见的“上传并公开词典”按钮才会写入云端。按钮在文件、名称、同意选项或云端连接尚未就绪时显示为不可用。公开内容仅包括词典名称和词条，不包括转换文本、Word 文档或原文件名。词条为用户提供，不代表官方字表。

使用时展开“使用公共词典”，开启使用开关并选择具体词典。云端预设了《【简体→规范繁体】补充词汇》，在简体转规范繁场景下建议勾选使用，欢迎共同维护。

个人词典优先于公共词典，公共词典优于默认字表；公共词典相同原词有冲突时，以较新发布的版本为准。关闭公共词典或切换到其他转换方向后，公共词条不参与转换。

上传时可选择“新建公共词典”或“补充现有公共词典”。补充现有词典会合并词条；若原词已经存在，以本次上传的替换词覆盖。

公共词典由@alzco维护，上传之后如需修改、删除词典，请联系本人或到[GitHub项目主页Issues区](https://github.com/alzco/Chinese-T-S-DocConverter/issues)留言。

### 连接已有 Supabase 项目

1. 在 Supabase SQL Editor 执行 [`supabase/schema.sql`](supabase/schema.sql)。脚本创建词典表、校验和限流触发器，并启用 RLS：发布密钥可读取启用的词典，但不能直接写表。
2. 部署 [`supabase/functions/public-dictionaries/index.ts`](supabase/functions/public-dictionaries/index.ts) Edge Function。新建和补充词典都通过该函数完成，数据库 Secret 只存在于 Supabase 函数环境中。
3. 从项目设置取得项目 URL 和 **Publishable Key**。此密钥只用于读取公共词典和调用投稿函数，可以安全地配置到应用环境中；不要把数据库 Secret 写进仓库。
4. 本地将 [`.streamlit/secrets.example.toml`](.streamlit/secrets.example.toml) 复制为 `.streamlit/secrets.toml` 并填写；线上在 Streamlit 应用 Settings → Secrets 填写同样内容：

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
publishable_key = "YOUR_PUBLISHABLE_KEY"
```

5. 重启应用，上传一份非敏感的测试词典并主动公开；在另一个浏览器会话中刷新公共词典列表，选择它并验证转换结果。删除测试数据可在 Supabase Dashboard 中操作。

未配置连接时，公开与使用公共词典的开关不可用，其他功能正常。配置后连接失败会显示重试提示；已开启公共词典时会暂停转换，避免悄悄忽略所选词典。本地真实 Secrets 文件已被忽略。

### 存储与维护

- 每份 JSON 最多 128 KB、500 个词条；原词最多 64 字，替换词最多 256 字，不能为空。
- 相同词条内容按摘要去重，不因改名重复发布。列表展示最新 100 份启用的词典，缓存 60 秒，也可手动刷新。
- 当前为无需账号的主动公开模式：每个会话每分钟最多提交一次，数据库全局每分钟最多接收 10 份。基础限流不能代替账号管理；大量开放投稿时应增加登录和审核。
- 维护者可在 Supabase Dashboard 将词典的 `active` 设为 `false` 以隐藏。隐藏的相同内容不会被重复上传重新启用。
- 上传的词典独立保存在 Supabase，不依赖 Streamlit 临时磁盘。数据库密钥轮换、项目配额及维护由项目所有者管理。

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

## 测试

```sh
python -B -m unittest discover -s tests -v
```

覆盖上游文件校验、配置加载、相容汉字正规化、混合简繁输入、语义词组、Word 格式与脚注尾注、下载包完整性，以及语言对调、选项联动等 Streamlit 交互。
