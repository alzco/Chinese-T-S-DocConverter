"""Streamlit interface for standard traditional Chinese conversion."""
import hashlib
import io
import json

import docx2txt
import streamlit as st

from document_converter import DocumentConverter
from opencc_converter import CustomOpenCC, DATA_DIR, validate_dictionary
from resources import DOWNLOADS, SOURCE, UPSTREAM_URL, TABLE_SOURCE_URL, TABLE_PDF_URL, dictionary_bundle

st.set_page_config(page_title='规范汉字繁简转换工具', page_icon='字', layout='wide')
st.markdown("""
<style>
.stApp { background: #f5f7f9; color: #203246; }
[data-testid="stMainBlockContainer"] {
    max-width: 1060px; padding-top: 2.8rem; padding-bottom: 2.5rem;
}
[data-testid="stHeadingWithActionElements"] h1 {
    font-family: inherit;
    font-size: clamp(1.65rem, 3.5vw, 2.4rem); font-weight: 700;
    letter-spacing: .035em; color: #203246; padding-bottom: .45rem;
}
[data-testid="stHeadingWithActionElements"] h1::before {
    content: ""; display: block; width: 36px; height: 4px;
    background: #24766b; border-radius: 3px; margin-bottom: 1.15rem;
}
h3 { color: #203246; font-size: 1.05rem !important; }
[data-testid="stCaptionContainer"] { color: #65758a; line-height: 1.75; }
.st-key-conversion_settings, .st-key-workspace {
    background: #fff; border: 1px solid #e0e7ed !important;
    border-radius: 16px !important; padding: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(32, 50, 70, .035);
}
.st-key-conversion_settings [data-testid="stMarkdownContainer"] p {
    color: #607084; font-size: .9rem; line-height: 1.8;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input { border-radius: 9px; }
[data-testid="stTextArea"] textarea { line-height: 1.85; }
[data-testid="stTabs"] [role="tablist"] {
    background: #f0f4f6; padding: 5px; border-radius: 11px;
    gap: 5px; margin-bottom: 1.2rem;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px; padding: .65rem 1.4rem; height: auto;
    color: #607084; flex: 1;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: #fff; color: #206b61;
    box-shadow: 0 1px 5px rgba(32, 50, 70, .09);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
[data-testid="stFileUploaderDropzone"] {
    background: #f7faf9; border: 1px dashed #9dbdb6;
    border-radius: 12px; padding: 1.8rem 1.2rem;
}
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
    border-radius: 9px; min-height: 2.65rem;
}
[data-testid="stBaseButton-primary"] {
    background-color: #24766b; border-color: #24766b; color: #fff;
}
[data-testid="stBaseButton-primary"]:hover {
    background-color: #1b6057; border-color: #1b6057; color: #fff;
}
[data-testid="stExpander"] details {
    background: #fff; border-color: #e0e7ed; border-radius: 11px;
}
a { color: #24766b; }
.st-key-swap_languages button { font-size: 1.3rem; color: #24766b; }
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding-top: 1.6rem; }
    .st-key-conversion_settings, .st-key-workspace { padding: 1rem !important; }
    [data-testid="stTabs"] [role="tab"] { padding: .6rem .8rem; }
}
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


with st.container(border=True, key='conversion_settings'):
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

with st.expander('自定义词典'):
    uploaded_dictionary = st.file_uploader('导入 JSON 词典', type=['json'], key='dictionary_upload')
    if uploaded_dictionary is not None:
        fingerprint = hashlib.sha256(uploaded_dictionary.getvalue()).hexdigest()
        if fingerprint != st.session_state.get('dictionary_imported'):
            try:
                st.session_state.custom_dict = validate_dictionary(json.loads(uploaded_dictionary.getvalue().decode('utf-8-sig')))
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


def convert_input():
    converter = CustomOpenCC(st.session_state.scheme)
    converter.custom_dict = dict(st.session_state.custom_dict)
    st.session_state.output_text = converter.convert(st.session_state.get('input_text', ''))


def clear_text():
    st.session_state.input_text = ''
    st.session_state.output_text = ''


def load_example():
    st.session_state.input_text = '为众人说《西厢记》：两晋异体字、绿色记录、启用线索。\n他看着书，研究著作；皇后以后读书，白云与云云，里面与一里路。'
    convert_input()


with st.container(border=True, key='workspace'):
    file_tab, text_tab = st.tabs(['文档转换', '文本转换'])
    with text_tab:
        left, right = st.columns(2)
        left.text_area('输入文本', key='input_text', height=260)
        right.text_area('转换结果', key='output_text', height=260)
        buttons = st.columns([2, 1, 1])
        buttons[0].button('转换文本', type='primary', on_click=convert_input, key='convert_text_btn', use_container_width=True)
        buttons[1].button('示例', on_click=load_example, use_container_width=True)
        buttons[2].button('清空', on_click=clear_text, key='clear_text_btn', use_container_width=True)
        if st.session_state.get('output_text'):
            st.download_button('下载文本', st.session_state.output_text, '转换结果.txt', 'text/plain')

    with file_tab:
        st.caption('支持 TXT、Markdown、DOCX；Word 保留格式，并转换脚注、尾注。')
        uploaded = st.file_uploader('选择文档', type=['txt', 'md', 'docx'], key='document_upload')
        if uploaded is not None:
            content = uploaded.getvalue()
            identity = (uploaded.name, hashlib.sha256(content).hexdigest(), selected,
                        json.dumps(st.session_state.custom_dict, ensure_ascii=False))
            if st.button('转换文档', type='primary'):
                try:
                    with st.spinner('正在转换…'):
                        converter = DocumentConverter(selected, st.session_state.custom_dict)
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
