"""Streamlit interface for standard traditional Chinese conversion."""
import base64
import hashlib
import io
import json
import time

import docx2txt
import streamlit as st

from public_dictionary import (PublicDictionaryStore, PublicDictionaryError,
                               parse_upload, select_public_dictionary)
from document_converter import DocumentConverter
from opencc_converter import CustomOpenCC, DATA_DIR, validate_dictionary
from resources import DOWNLOADS, SOURCE, UPSTREAM_URL, TABLE_SOURCE_URL, TABLE_PDF_URL, dictionary_bundle

st.set_page_config(page_title='规范汉字繁简转换工具', page_icon='字', layout='wide')
st.markdown("""
<style>
.stApp { background: #fff; color: #202124; }
[data-testid="stMainBlockContainer"] { max-width: 980px; padding: 3rem 2rem; }
[data-testid="stHeadingWithActionElements"] h1 {
    font-family: inherit; font-size: clamp(1.8rem, 3.5vw, 2.5rem);
    font-weight: 700; letter-spacing: -.025em; color: #202124;
    display: flex; align-items: center; gap: .7rem;
}
[data-testid="stHeadingWithActionElements"] h1::before {
    content: ""; display: inline-block; flex: 0 0 2.2rem; width: 2.2rem; height: 2.2rem;
    background: center / contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='11' fill='%231a73e8'/%3E%3Cpath d='M13 17h19m-5-6 6 6-6 6M35 31H16m5 6-6-6 6-6' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}
h3 { font-size: 1.05rem !important; font-weight: 600 !important; }
[data-testid="stCaptionContainer"] { color: #70757a; line-height: 1.6; }
.st-key-conversion_settings { border-bottom: 1px solid #e8eaed; padding-bottom: 1rem; }
.st-key-conversion_settings [data-testid="stMarkdownContainer"] p { color: #70757a; font-size: .875rem; }
[data-testid="stTextArea"] textarea { line-height: 1.8; background: #f8f9fa; }
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button { border-radius: 6px; box-shadow: none; }
[data-testid="stBaseButton-primary"] { background: #1a73e8; border-color: #1a73e8; }
[data-testid="stBaseButton-primary"]:hover { background: #155fc0; border-color: #155fc0; }
[data-testid="stExpander"] details { border-color: #e8eaed; border-radius: 6px; box-shadow: none; }
[data-testid="stTabs"] [role="tablist"] { gap: 1.5rem; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #1a73e8; }
.st-key-swap_languages button { color: #5f6368; }
a { color: #1a73e8; }
@media (max-width: 640px) { [data-testid="stMainBlockContainer"] { padding: 1.5rem 1rem; } }
</style>
""", unsafe_allow_html=True)

st.title('规范汉字繁简转换工具')
st.caption('基于openCC与《通用规范汉字表》的中文简繁转换工具，支持自定义词典功能。')

# Only expose useful, directly supported directions. Internal OpenCC configuration
# names and specialized normalization modes are kept out of the main interface.
DIRECTIONS = {
    '简体': {'规范繁体': 's2gov', '台湾繁体': 's2tw', '香港繁体': 's2hk'},
    '规范繁体': {'简体': 'gov2s', '台湾繁体': 't2tw', '香港繁体': 't2hk'},
    '台湾繁体': {'简体': 'tw2s', '规范繁体': 't2gov'},
    '香港繁体': {'简体': 'hk2s', '规范繁体': 't2gov'},
    '其他繁体': {'简体': 'gov2s', '规范繁体': 't2gov', '台湾繁体': 't2tw', '香港繁体': 't2hk'},
}

def swap_languages():
    source = st.session_state.source_language
    target = st.session_state.target_language
    if source in DIRECTIONS[target]:
        st.session_state.source_language = target
        st.session_state.target_language = source
        st.session_state.output_text = ''


with st.container(border=False, key='conversion_settings'):
    st.subheader('转换方案')
    source_column, swap_column, target_column = st.columns([5, 1, 5], vertical_alignment='bottom')
    source_language = source_column.selectbox('源语言', list(DIRECTIONS), key='source_language',
        help='不确定繁体字形所属地区，或原文混用多种繁体字形时，可选“其他繁体”。')
    target_options = list(DIRECTIONS[source_language])
    if st.session_state.get('target_language') not in target_options:
        st.session_state.target_language = target_options[0]
    target_language = target_column.selectbox('目标语言', target_options, key='target_language')
    can_swap = source_language in DIRECTIONS[target_language]
    swap_column.button('⇄', key='swap_languages', on_click=swap_languages,
        use_container_width=True, disabled=not can_swap,
        help='对调源语言与目标语言' if can_swap else '“其他繁体”包含多种字形，不能作为明确的转换目标。')
    selected = DIRECTIONS[source_language][target_language]
    st.session_state.scheme = selected

    if target_language == '规范繁体':
        purpose = ('将简体转为规范繁体，同时统一原文中已有的繁体和异体字形' if source_language == '简体'
                   else '将原文中的繁体字形统一为规范繁体')
        explanation = f'{purpose}，采用依据《通用规范汉字表》整理的转换方案。'
    elif target_language == '简体':
        explanation = '将繁体文字转换为简体，适合日常阅读和简体文稿整理。'
    else:
        explanation = f'将原文转换为{target_language}字形，保留原有用词，不进行地区词汇替换。'
    st.write(explanation + ' 文本和上传的文档均使用当前选择。')

if 'custom_dict' not in st.session_state:
    st.session_state.custom_dict = {}

def cloud_store():
    try:
        settings = st.secrets.get('supabase', {})
    except FileNotFoundError:
        return None
    if not settings.get('url') or not settings.get('secret_key'):
        return None
    return PublicDictionaryStore(settings['url'], settings['secret_key'])


@st.cache_data(ttl=60, show_spinner=False)
def cloud_list(url, _store):
    return _store.list()


try:
    store = cloud_store()
except PublicDictionaryError:
    store = None

with st.expander('自定义本地词典'):
    st.caption('JSON 格式须为“原词: 替换词”的对象，例如：`{"计算机": "信息处理设备", "线上会议": "在线会议"}`。文件使用 UTF-8 编码，最多 500 个词条、128 KB。')
    uploaded_dictionary = st.file_uploader('导入 JSON 词典', type=['json'], key='dictionary_upload')
    if uploaded_dictionary is not None:
        fingerprint = hashlib.sha256(uploaded_dictionary.getvalue()).hexdigest()
        if fingerprint != st.session_state.get('dictionary_imported'):
            try:
                st.session_state.custom_dict = parse_upload(uploaded_dictionary.getvalue())
                st.session_state.dictionary_imported = fingerprint
            except (ValueError, UnicodeError) as error:
                st.error(str(error))
    with st.form('dictionary_entry', clear_on_submit=True):
        left, right = st.columns(2)
        source = left.text_input('原词')
        target = right.text_input('替换为')
        if st.form_submit_button('添加词条'):
            try:
                st.session_state.custom_dict.update(validate_dictionary({source: target}))
            except ValueError as error:
                st.error(str(error))
    if st.session_state.custom_dict:
        chosen = st.selectbox('已有词条', list(st.session_state.custom_dict), format_func=lambda k: f'{k} → {st.session_state.custom_dict[k]}')
        if st.button('删除词条'):
            del st.session_state.custom_dict[chosen]
            st.rerun()
    st.download_button('导出自定义词典', json.dumps(st.session_state.custom_dict, ensure_ascii=False, indent=2), 'custom_dict.json', 'application/json')
    st.caption('自定义替换先于繁简转换执行。')

with st.expander('上传到公共词典', expanded=True):
    upload_rows = []
    if store is not None:
        try:
            upload_rows = cloud_list(store.url, store)
        except PublicDictionaryError as error:
            st.error(str(error))
    upload_mode = st.radio('上传方式', ['新建公共词典', '补充现有公共词典'],
                           horizontal=True, key='public_upload_mode')
    target_dictionary_id = None
    if upload_mode == '补充现有公共词典':
        upload_labels = {row['id']: f"{row['name']} · {len(row['mapping'])} 词" for row in upload_rows}
        target_dictionary_id = st.selectbox(
            '选择现有词典', list(upload_labels), format_func=upload_labels.get,
            disabled=not upload_rows, placeholder='暂无可更新的公共词典',
            key='target_public_dictionary')
    public_upload = st.file_uploader('选择要公开的 JSON 词典', type=['json'], key='public_upload')
    public_name = ''
    if upload_mode == '新建公共词典':
        public_name = st.text_input('公共词典名称', max_chars=60, key='public_name')
    public_mapping = None
    if public_upload is not None:
        try:
            public_mapping = parse_upload(public_upload.getvalue())
            st.caption(f'共 {len(public_mapping)} 个词条')
            st.json(public_mapping, expanded=False)
        except ValueError as error:
            st.error(str(error))
    public_fingerprint = hashlib.sha256(public_upload.getvalue()).hexdigest() if public_upload else 'empty'
    consent = st.checkbox('同意将这份词典公开，供其他用户选择使用', key='consent_' + public_fingerprint)
    if store is None:
        st.caption('云端尚未连接，完成配置后即可上传。')
    if upload_mode == '补充现有公共词典':
        st.caption('上传内容将合并到所选词典；遇到相同原词时，以本次上传的替换词为准。')
    st.caption('仅公开词典名称与词条，用于简体转规范繁体；不会公开你的文本和 Word 文档。')
    ready_target = bool(public_name.strip()) if upload_mode == '新建公共词典' else bool(target_dictionary_id)
    publish_label = '新建并公开词典' if upload_mode == '新建公共词典' else '合并到现有词典'
    if st.button(publish_label, key='publish_dictionary', type='primary',
                 disabled=store is None or not public_mapping or not ready_target or not consent):
        if time.time() - st.session_state.get('last_publication', 0) < 60:
            st.warning('请稍等一分钟再提交新的词典。')
        else:
            try:
                if upload_mode == '新建公共词典':
                    created = store.publish(public_name, public_upload.getvalue())
                    message = ('词典已公开，可在下方公共词典中选择。' if created
                               else '相同内容已提交，无需重复上传。')
                else:
                    store.merge_into(target_dictionary_id, public_upload.getvalue())
                    message = '词条已合并到现有公共词典。'
                st.session_state.last_publication = time.time()
                cloud_list.clear()
                st.success(message)
            except (PublicDictionaryError, ValueError) as error:
                st.error(str(error))

cloud_failed = False
with st.expander('使用公共词典'):
    public_enabled = st.checkbox('使用云端用户公共词典', key='use_public_dictionary',
                                 disabled=store is None or selected != 's2gov')
    public_rows = []
    public_ids = []
    if store is None:
        st.caption('公共词典尚未接入云端，个人词典和文件转换可正常使用。')
    elif selected != 's2gov':
        st.caption('仅在“简体 → 规范繁体”方向生效。')
    elif public_enabled:
        if st.button('刷新词典列表'):
            cloud_list.clear()
        try:
            public_rows = cloud_list(store.url, store)
            labels = {row['id']: f"{row['name']} · {len(row['mapping'])} 词 · {row['id'][:6]}" for row in public_rows}
            default_ids = [row['id'] for row in public_rows
                           if row['name'] == '专有名词与词组（简体转规范繁体）']
            public_ids = st.multiselect('选择要使用的词典', list(labels), default=default_ids,
                                        format_func=labels.get)
            if not public_rows:
                st.caption('暂时没有公共词典，你可以从上方上传并公开第一份。')
            for row in public_rows:
                if row['id'] in public_ids:
                    with st.expander(labels[row['id']]):
                        st.json(row['mapping'])
        except PublicDictionaryError as error:
            cloud_failed = True
            st.error(str(error) + ' 重新连接或关闭公共词典后再转换。')
    st.caption('默认关闭。公共词典命中的专有名词会保留词典指定的最终字形；词典间有冲突时采用较新提交的词条。')

public_dictionary, conflicts = select_public_dictionary(
    public_rows, public_ids, public_enabled, selected)
st.session_state.active_public_dictionary = public_dictionary
if conflicts:
    st.caption(f'所选公共词典有 {conflicts} 个冲突词条，已采用较新提交的内容。')


def convert_input():
    converter = CustomOpenCC(st.session_state.scheme)
    converter.custom_dict = dict(st.session_state.custom_dict)
    converter.public_dict = dict(st.session_state.active_public_dictionary)
    st.session_state.output_text = converter.convert(st.session_state.get('input_text', ''))


def clear_text():
    st.session_state.input_text = ''
    st.session_state.output_text = ''


def load_example():
    st.session_state.input_text = '为众人说《西厢记》：两晋异体字、绿色记录、启用线索。\n他看着书，研究著作；皇后以后读书，白云与云云，里面与一里路。'
    convert_input()


with st.container(border=False, key='workspace'):
    file_tab, text_tab = st.tabs(['文档转换', '文本转换'])
    with text_tab:
        left, right = st.columns(2)
        left.text_area('输入文本', key='input_text', height=260)
        right.text_area('转换结果', key='output_text', height=260)
        buttons = st.columns([2, 1, 1])
        buttons[0].button('转换文本', type='primary', on_click=convert_input, key='convert_text_btn', use_container_width=True, disabled=cloud_failed)
        buttons[1].button('示例', on_click=load_example, use_container_width=True, disabled=cloud_failed)
        buttons[2].button('清空', on_click=clear_text, key='clear_text_btn', use_container_width=True)
        if st.session_state.get('output_text'):
            copy_payload = base64.b64encode(st.session_state.output_text.encode()).decode()
            st.iframe(f'''<button id="copy" style="font:14px system-ui;padding:9px 16px;border:1px solid #dadce0;border-radius:6px;background:#fff;color:#202124;cursor:pointer">复制文本</button>
<script>const text=new TextDecoder().decode(Uint8Array.from(atob('{copy_payload}'),c=>c.charCodeAt(0)));const b=document.getElementById('copy');b.onclick=async()=>{{await navigator.clipboard.writeText(text);b.textContent='已复制';setTimeout(()=>b.textContent='复制文本',1500);}};</script>''', height=48)

    with file_tab:
        st.caption('支持 TXT、Markdown、DOCX；Word 保留格式，并转换脚注、尾注。')
        uploaded = st.file_uploader('选择文档', type=['txt', 'md', 'docx'], key='document_upload')
        if uploaded is not None:
            content = uploaded.getvalue()
            identity = (uploaded.name, hashlib.sha256(content).hexdigest(), selected,
                        json.dumps(st.session_state.custom_dict, ensure_ascii=False, sort_keys=True),
                        json.dumps(public_dictionary, ensure_ascii=False, sort_keys=True))
            if st.button('转换文档', type='primary', disabled=cloud_failed):
                try:
                    with st.spinner('正在转换…'):
                        converter = DocumentConverter(
                            selected, st.session_state.custom_dict, public_dictionary)
                        extension = uploaded.name.rsplit('.', 1)[-1].lower()
                        result = converter.convert_file(content, extension)
                        if isinstance(result, str):
                            result = result.encode('utf-8')
                        st.session_state.document_result = (identity, result, extension)
                except Exception as error:
                    st.error(f'转换失败：{error}')
            saved = st.session_state.get('document_result')
            if saved and saved[0] == identity:
                _, data, extension = saved
                mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if extension == 'docx' else 'text/plain'
                st.download_button('下载转换后的文档', data, '转换后_' + uploaded.name, mime, type='primary')
                with st.expander('预览文本'):
                    try:
                        preview = docx2txt.process(io.BytesIO(data)) if extension == 'docx' else data.decode('utf-8')
                        st.text_area('文档内容', preview, height=260, disabled=True)
                    except Exception:
                        st.caption('此文件无法预览，请下载查看。')

st.divider()
with st.expander('字表与词库下载'):
    st.markdown(f'[《通用规范汉字表》（2013）PDF]({TABLE_PDF_URL}) · [教育部发布页]({TABLE_SOURCE_URL})')
    label = st.selectbox('转换词库（TXT）', list(DOWNLOADS), key='resource')
    filename = DOWNLOADS[label]
    left, right = st.columns(2)
    left.download_button('下载所选词库', (DATA_DIR / filename).read_bytes(), filename, 'text/plain', key='download_dictionary')
    right.download_button('下载全部词库与配置', dictionary_bundle(), 'tonggui-opencc-dictionaries.zip', 'application/zip', key='download_bundle')
    st.caption(f"词库版本 {SOURCE['commit'][:8]} · Apache-2.0")
st.caption(f'规范繁体方案与词库：[TerryTian-tech / OpenCC 规范繁体]({UPSTREAM_URL}) · 引擎：[OpenCC](https://github.com/BYVoid/OpenCC)')
st.caption('方案对部分字形另有调整，转换结果仍需校对。')
st.caption('GitHub 项目：[alzco/Chinese-T-S-DocConverter](https://github.com/alzco/Chinese-T-S-DocConverter)')
