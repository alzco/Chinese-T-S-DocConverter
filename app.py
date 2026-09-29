"""Streamlit interface for standard traditional Chinese conversion."""
import hashlib
import io
import json

import docx2txt
import streamlit as st

from document_converter import DocumentConverter
from opencc_converter import CustomOpenCC, DATA_DIR, validate_dictionary
from resources import DOWNLOADS, SOURCE, UPSTREAM_URL, TABLE_SOURCE_URL, TABLE_PDF_URL, dictionary_bundle

st.set_page_config(page_title='规范繁体转换', page_icon='字', layout='wide')
st.title('规范繁体转换')
st.caption('文本与 Word 简繁转换，默认采用规范繁体方案。')

SCHEMES = {
    's2gov': '简体 → 规范繁体',
    't2gov': '繁体 → 规范繁体',
    'gov2s': '繁体 → 简体（通规方案）',
    't2new': '繁体旧字形 → 新字形',
    't2gov_keep_simp': '繁体 → 规范繁体（保留简体）',
    's2t': '简体 → 繁体（OpenCC 原版）',
    't2s': '繁体 → 简体（OpenCC 原版）',
    's2tw': '简体 → 台湾繁体',
    's2twp': '简体 → 台湾繁体（台湾用词）',
    's2hk': '简体 → 香港繁体',
    'tw2s': '台湾繁体 → 简体',
    'hk2s': '香港繁体 → 简体',
    'tw2sp': '台湾繁体 → 简体（大陆用词）',
    't2tw': '繁体 → 台湾繁体',
    't2hk': '繁体 → 香港繁体',
    'hk2t': '香港繁体 → 繁体（OpenCC 原版）',
    'tw2t': '台湾繁体 → 繁体（OpenCC 原版）',
    't2jp': '繁体 → 日文新字体',
    'jp2t': '日文新字体 → 繁体（OpenCC 原版）',
}
selected = st.selectbox('转换方案', list(SCHEMES), format_func=SCHEMES.get, key='scheme')
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


text_tab, file_tab = st.tabs(['文本转换', '文档转换'])
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
