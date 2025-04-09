#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenCC Converter Web Application
A Streamlit-based web interface for simplified-traditional Chinese conversion
with support for custom dictionaries and document processing.
"""

import streamlit as st
import json
import os
import io
import base64
from opencc_converter import CustomOpenCC
from document_converter import DocumentConverter

# Set page configuration
st.set_page_config(
    page_title="OpenCC Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS
st.markdown("""
<style>
    body {
        font-family: 'Google Sans', 'Segoe UI', Roboto, sans-serif;
        color: #202124;
        background-color: #ffffff;
    }
    .main {
        padding: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .stTextArea textarea {
        font-size: 1rem;
        min-height: 150px;
        border-radius: 8px;
        border: 1px solid #dadce0;
        padding: 12px;
        transition: border-color 0.3s;
    }
    .stTextArea textarea:focus {
        border-color: #1a73e8;
        box-shadow: 0 0 0 1px #1a73e8;
    }
    .custom-dict-entry {
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 8px;
        background-color: #f8f9fa;
        border: 1px solid #dadce0;
    }
    .title-area {
        text-align: center;
        margin-bottom: 2.5rem;
        padding: 2.5rem 2rem;
        background-color: #f8f9fa;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .title-area::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background-color: #1a73e8;
    }
    .title-area h1 {
        font-weight: 700;
        color: #202124;
        margin-bottom: 0.8rem;
        font-size: 2.4rem;
        letter-spacing: -0.5px;
    }
    .title-area p {
        color: #5f6368;
        font-size: 1.1rem;
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.5;
    }
    /* 按钮样式 */
    .stButton button {
        background-color: #1a73e8;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .stButton button:hover {
        background-color: #1765cc;
        box-shadow: 0 2px 5px rgba(0,0,0,0.16), 0 2px 5px rgba(0,0,0,0.23);
        transform: translateY(-1px);
    }
    .stButton button:active {
        background-color: #1557b0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        transform: translateY(1px);
    }
    /* 添加波纹效果 */
    .stButton button::after {
        content: '';
        display: block;
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        pointer-events: none;
        background-image: radial-gradient(circle, #fff 10%, transparent 10.01%);
        background-repeat: no-repeat;
        background-position: 50%;
        transform: scale(10, 10);
        opacity: 0;
        transition: transform .5s, opacity 1s;
    }
    .stButton button:active::after {
        transform: scale(0, 0);
        opacity: 0.3;
        transition: 0s;
    }
    /* 删除卡片样式 */
    /* 自定义词典侧边栏 */
    .dict-sidebar {
        background-color: #f8f9fa;
        border-left: 1px solid #dadce0;
        padding: 1rem;
        height: 100%;
    }
    /* 自定义按钮样式 */
    .custom-btn {
        background-color: #1a73e8;
        color: white !important;
        border: none;
        padding: 10px 18px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 8px 4px 0;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.3s ease;
        width: auto;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .custom-btn:hover {
        background-color: #1765cc;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    .custom-btn:active {
        background-color: #1557b0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        transform: translateY(1px);
    }
    /* 清空按钮样式 */
    .clear-btn {
        background-color: #f8f9fa;
        color: #5f6368 !important;
        border: 1px solid #dadce0;
        padding: 10px 18px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.3s ease;
        width: auto;
        font-weight: 500;
    }
    .clear-btn:hover {
        background-color: rgba(95, 99, 104, 0.04);
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .clear-btn:active {
        background-color: rgba(95, 99, 104, 0.08);
        transform: translateY(1px);
    }
    /* 简约分割线 */
    .simple-divider {
        height: 1px;
        background-color: #e0e0e0;
        margin: 2rem 0;
        width: 100%;
    }
    /* 下载按钮样式 */
    a[download] {
        display: inline-block;
        background-color: #1a73e8;
        color: white !important;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
        margin-top: 1rem;
        transition: background-color 0.3s;
    }
    a[download]:hover {
        background-color: #1765cc;
    }
    /* 选择框样式 */
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 4px;
    }
    /* 文件上传区域样式 */
    .stFileUploader div[data-testid="stFileUploader"] {
        border-radius: 8px;
        border: 1px dashed #dadce0;
        padding: 1rem;
    }

    /* 主要内容区和侧边栏布局 */
    .main-content {
        display: flex;
        flex-direction: row;
    }
    .content-area {
        flex: 3;
        padding-right: 1rem;
    }
    .sidebar-area {
        flex: 1;
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #dadce0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for custom dictionary
if 'custom_dict' not in st.session_state:
    st.session_state.custom_dict = {}

if 'dict_file_path' not in st.session_state:
    st.session_state.dict_file_path = "custom_dict.json"



# Title and description
st.markdown("<div class='title-area'><h1>OpenCC 繁简转换工具</h1><p>基于 OpenCC 的中文简繁转换工具，支持自定义词典和文档处理</p></div>", unsafe_allow_html=True)

# 创建主要内容区和侧边栏的布局
st.markdown("<div class='main-content'>", unsafe_allow_html=True)
st.markdown("<div class='content-area'>", unsafe_allow_html=True)

# 转换设置区域
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("转换设置")

# Conversion direction
conversion_options = {
    's2t': '简体 → 繁体',
    't2s': '繁体 → 简体',
    's2tw': '简体 → 台湾繁体',
    'tw2s': '台湾繁体 → 简体',
    's2hk': '简体 → 香港繁体',
    'hk2s': '香港繁体 → 简体',
    's2twp': '简体 → 台湾繁体（台湾用词）',
    'tw2sp': '台湾繁体 → 简体（大陆用词）',
    't2tw': '繁体 → 台湾繁体',
    'hk2t': '香港繁体 → 繁体',
    't2hk': '繁体 → 香港繁体',
    't2jp': '繁体 → 日文新字体',
    'jp2t': '日文新字体 → 繁体',
    'tw2t': '台湾繁体 → 繁体'
}

# 初始化转换方向的session state
if 'source_lang' not in st.session_state:
    st.session_state.source_lang = '简体'
    st.session_state.target_lang = '繁体'
    st.session_state.current_direction = 's2t'

# 左右两栏设置转换方向
col1, col3 = st.columns(2)

with col1:
    # 源语言选择
    source_options = ['简体', '繁体', '台湾繁体', '香港繁体', '日文新字体']
    source_lang = st.selectbox("源语言", options=source_options, index=source_options.index(st.session_state.source_lang))

with col3:
    # 目标语言选择
    target_options = ['简体', '繁体', '台湾繁体', '香港繁体', '日文新字体']
    target_lang = st.selectbox("目标语言", options=target_options, index=target_options.index(st.session_state.target_lang))
    
# 使用CSS隐藏按钮
st.markdown("""
<style>
    div[data-testid="stButton"][aria-describedby="swap_btn_help"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 隐藏的按钮，用于后台逻辑
if st.button("调换方向", key="swap_btn", help="调换源语言和目标语言"):
    # 交换源语言和目标语言
    st.session_state.source_lang, st.session_state.target_lang = st.session_state.target_lang, st.session_state.source_lang
    # 根据新的语言组合选择相应的转换方向
    st.rerun()

# 根据选择的语言确定转换方向
st.session_state.source_lang = source_lang
st.session_state.target_lang = target_lang

# 根据选择的语言组合确定转换方向
direction_map = {
    ('简体', '繁体'): 's2t',
    ('繁体', '简体'): 't2s',
    ('简体', '台湾繁体'): 's2tw',
    ('台湾繁体', '简体'): 'tw2s',
    ('简体', '香港繁体'): 's2hk',
    ('香港繁体', '简体'): 'hk2s',
    ('繁体', '台湾繁体'): 't2tw',
    ('香港繁体', '繁体'): 'hk2t',
    ('繁体', '香港繁体'): 't2hk',
    ('繁体', '日文新字体'): 't2jp',
    ('日文新字体', '繁体'): 'jp2t',
    ('台湾繁体', '繁体'): 'tw2t'
}

# 特殊情况处理
if (source_lang, target_lang) == ('简体', '台湾繁体'):
    # 提供选项切换普通台湾繁体和台湾用词
    use_taiwan_terms = st.checkbox("使用台湾用词", value=True)
    selected_conversion = 's2twp' if use_taiwan_terms else 's2tw'
else:
    # 正常情况
    lang_key = (source_lang, target_lang)
    if lang_key in direction_map:
        selected_conversion = direction_map[lang_key]
    else:
        # 默认值
        selected_conversion = 's2t'
        st.warning(f"不支持从 {source_lang} 到 {target_lang} 的转换，已默认使用简体到繁体转换")



# 文本转换区域
st.markdown("<div class='simple-divider'></div>", unsafe_allow_html=True)
st.subheader("文本转换")

# Create two columns for the main layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("输入文本")
    # 使用随机键来强制清空输入框
    if 'input_text_key' not in st.session_state:
        st.session_state.input_text_key = 0
    
    # 添加回调函数处理Cmd+Enter
    def on_text_change():
        if 'input_text' in st.session_state and st.session_state.input_text:
            # 创建转换器
            converter = CustomOpenCC(selected_conversion)
            
            # 添加自定义词典条目
            for source, target in st.session_state.custom_dict.items():
                converter.add_custom_mapping(source, target)
            
            # 执行转换
            converted_text = converter.convert(st.session_state.input_text)
            
            # 更新session state中的转换结果
            st.session_state.converted_text = converted_text
            st.rerun()
    
    input_text = st.text_area("", height=300, placeholder="请在此输入要转换的文本...\n\n提示: 输入文本后按Cmd+Enter可直接转换", 
                           key="input_text", on_change=on_text_change)
    
    # 文本转换按钮
    convert_col1, convert_col2 = st.columns([3, 3])
    with convert_col1:
        if st.button("转换文本", type="primary", key="convert_text_btn", use_container_width=True):
            if input_text:
                # Create converter with selected configuration
                converter = CustomOpenCC(selected_conversion)
                
                # Add custom dictionary entries
                for source, target in st.session_state.custom_dict.items():
                    converter.add_custom_mapping(source, target)
                
                # Perform conversion
                converted_text = converter.convert(input_text)
                
                # 更新session state中的转换结果
                st.session_state.converted_text = converted_text
                
                # 直接显示结果，不使用rerun
                # 注意：移除了对st.session_state.input_text的直接赋值，因为这会与文本区域widget冲突
            else:
                st.warning("请输入要转换的文本")
                
    with convert_col2:
        if st.button("清空", key="clear_text_btn", use_container_width=True):
            # 清空输入文本
            # 使用session_state来清空输入框
            if 'input_text_key' not in st.session_state:
                st.session_state.input_text_key = 0
            st.session_state.input_text_key += 1
            st.rerun()

with col2:
    output_col1, output_col2 = st.columns([3, 1])
    
    with output_col1:
        st.markdown("转换结果")
    
    with output_col2:
        # 标题
        st.markdown("")
    
    # 初始化session state用于存储转换结果
    if 'converted_text' not in st.session_state:
        st.session_state.converted_text = ""
    
    # 可编辑的转换结果文本区域
    edited_output = st.text_area("", value=st.session_state.converted_text, height=300, key="output_text")
    
    # 使用Streamlit的方式提供复制功能
    copy_col1, copy_col2 = st.columns([3, 1])
    
    with copy_col1:
        # 显示复制按钮的提示
        st.markdown("点击右侧按钮复制转换结果，或直接选中文本后使用Ctrl+C/Cmd+C复制")
    
    with copy_col2:
        # 使用JavaScript实现复制功能，更适合Streamlit Cloud
        if st.button("复制", key="copy_btn", use_container_width=True):
            # 使用JavaScript将文本复制到剪贴板
            js = f"""
            <script>
            const textToCopy = {json.dumps(edited_output)};
            
            // 尝试使用现代的Clipboard API
            async function copyToClipboard() {{
                try {{
                    await navigator.clipboard.writeText(textToCopy);
                    return true;
                }} catch (err) {{
                    return false;
                }}
            }}
            
            // 如果Clipboard API失败，使用后备方法
            function fallbackCopyToClipboard() {{
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                let success = false;
                try {{
                    success = document.execCommand('copy');
                }} catch (err) {{}}
                
                document.body.removeChild(textArea);
                return success;
            }}
            
            // 尝试复制并显示结果
            (async () => {{
                const success = await copyToClipboard() || fallbackCopyToClipboard();
                const message = document.createElement('div');
                message.style.position = 'fixed';
                message.style.top = '10px';
                message.style.left = '50%';
                message.style.transform = 'translateX(-50%)';
                message.style.padding = '10px 20px';
                message.style.borderRadius = '4px';
                message.style.zIndex = '9999';
                
                if (success) {{
                    message.style.backgroundColor = '#4CAF50';
                    message.style.color = 'white';
                    message.textContent = '已复制到剪贴板';
                }} else {{
                    message.style.backgroundColor = '#FFC107';
                    message.style.color = 'black';
                    message.textContent = '复制失败，请手动选中文本并使用Ctrl+C/Cmd+C';
                }}
                
                document.body.appendChild(message);
                setTimeout(() => document.body.removeChild(message), 3000);
            }})();
            </script>
            """
            st.components.v1.html(js, height=0)

# 文档转换区域
st.markdown("<div class='simple-divider'></div>", unsafe_allow_html=True)
st.subheader("文档转换")
st.markdown("""
<div style="margin-bottom: 1rem;">
    <p>上传文档，转换后下载。支持 .txt、.md 和 .docx 格式。</p>
    <p style="color: #d93025; font-size: 0.9rem; margin-top: 0.5rem;">注意：不支持.docx文档脚注和尾注部分的繁简转换，需后续手动处理。</p>
</div>
""", unsafe_allow_html=True)

# 文件上传组件
uploaded_file = st.file_uploader("选择文件", type=["txt", "md", "docx"])

if uploaded_file is not None:
    # 显示文件信息
    col1, col2 = st.columns(2)
    
    with col1:
        file_details = {
            "文件名": uploaded_file.name,
            "文件类型": uploaded_file.type,
            "文件大小": f"{uploaded_file.size / 1024:.2f} KB"
        }
        st.markdown("文件信息:")
        for k, v in file_details.items():
            st.markdown(f"**{k}**: {v}")
    
    with col2:
        # 文档转换按钮
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("转换文档", type="primary", key="convert_doc_btn", use_container_width=True):
            try:
                # 读取文件内容
                file_content = uploaded_file.getvalue()
                
                # 获取当前选择的转换配置
                current_conversion = selected_conversion
                
                # 创建文档转换器
                doc_converter = DocumentConverter(
                    opencc_config=current_conversion,
                    custom_dict=st.session_state.custom_dict
                )
                
                # 获取文件扩展名
                file_extension = uploaded_file.name.split(".")[-1].lower()
                
                # 根据文件类型进行转换
                if file_extension in ["txt", "md"]:
                    # 转换文本文件
                    converted_content = doc_converter.convert_file(file_content, file_extension)
                    
                    # 创建下载链接
                    b64 = base64.b64encode(converted_content.encode()).decode()
                    output_filename = f"converted_{uploaded_file.name}"
                    href = f'<a href="data:text/plain;base64,{b64}" download="{output_filename}">下载转换后的文件</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # 预览转换结果
                    with st.expander("预览转换结果", expanded=True):
                        st.text_area("", value=converted_content, height=300)
                
                elif file_extension == "docx":
                    # 转换Word文档
                    converted_content = doc_converter.convert_file(file_content, file_extension)
                    
                    # 创建下载链接
                    b64 = base64.b64encode(converted_content).decode()
                    output_filename = f"converted_{uploaded_file.name}"
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{output_filename}">下载转换后的文件</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # 显示成功信息
                    st.success(f"Word文档转换成功，请点击上方链接下载")
                    
                    # 提取并预览文本内容
                    try:
                        import docx2txt
                        text_content = docx2txt.process(io.BytesIO(file_content))
                        converted_text_content = doc_converter.convert_text(text_content)
                        
                        with st.expander("预览转换结果（仅文本内容）", expanded=True):
                            st.text_area("", value=converted_text_content, height=300)
                    except Exception as e:
                        st.warning(f"无法预览Word文档内容: {e}")
                
                else:
                    st.error(f"不支持的文件类型: {file_extension}")
            
            except Exception as e:
                st.error(f"转换文档时出错: {e}")



# 结束主要内容区域




# 自定义词典区域（侧边栏）
st.markdown("<div class='sidebar-area'>", unsafe_allow_html=True)
st.subheader("自定义词典")

# 添加简洁说明
st.markdown("""
<div style="margin-bottom: 1rem;">
    <p>你可以创建和管理词汇转换规则。</p>
    <p>加载词典 - 从指定的JSON文件中加载预先保存的自定义转换规则<br>
    保存词典 - 将当前的自定义转换规则保存到JSON文件中以便将来使用<br>
    添加词条 - 创建新的自定义转换规则，指定源词汇和目标词汇<br>
    删除词条 - 移除不再需要的自定义转换规则</p>
</div>
""", unsafe_allow_html=True)

# Dictionary file management
st.markdown("### 词典文件管理")
st.markdown("你可以上传已有的词典文件，或下载当前词典以备将来使用。")

# 上传和下载按钮并排
upload_col, download_col = st.columns(2)

# 上传词典文件
with upload_col:
    uploaded_file = st.file_uploader("上传词典文件", type=["json"], help="上传JSON格式的词典文件")
    if uploaded_file is not None:
        try:
            # 读取上传的文件内容
            dict_content = uploaded_file.read().decode('utf-8')
            uploaded_dict = json.loads(dict_content)
            st.session_state.custom_dict = uploaded_dict
            st.success(f"成功加载词典: {len(st.session_state.custom_dict)} 个条目")
        except Exception as e:
            st.error(f"加载词典失败: {e}")

# 下载当前词典
with download_col:
    if st.button("下载当前词典", use_container_width=True):
        # 将当前词典转换为JSON字符串
        json_str = json.dumps(st.session_state.custom_dict, ensure_ascii=False, indent=2)
        # 创建下载链接
        b64 = base64.b64encode(json_str.encode('utf-8')).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="custom_dict.json" class="custom-btn">点击下载词典文件</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        # 显示成功消息
        if len(st.session_state.custom_dict) > 0:
            st.success(f"已准备下载词典: {len(st.session_state.custom_dict)} 个条目")
        else:
            st.info("当前词典为空，将下载空词典文件")

# Add new dictionary entry
st.markdown("添加新词条")

# 源词汇和目标词汇输入框
source_term = st.text_input("源词汇", key="source_term_input")
target_term = st.text_input("目标词汇", key="target_term_input")

# 添加按钮
if st.button("添加词条", key="add_dict_entry_btn", use_container_width=True):
    if source_term and target_term:
        st.session_state.custom_dict[source_term] = target_term
        st.success(f"已添加词条: {source_term} → {target_term}")
        st.rerun()
    else:
        st.warning("源词汇和目标词汇不能为空")

# Display and manage dictionary entries
st.markdown("当前词典")
if st.session_state.custom_dict:
    for i, (source, target) in enumerate(list(st.session_state.custom_dict.items())):
        dict_entry_col1, dict_entry_col2 = st.columns([4, 1])
        with dict_entry_col1:
            st.markdown(f"**{source}** → {target}")
        with dict_entry_col2:
            if st.button("删除", key=f"del_{i}_{source}", use_container_width=True):
                del st.session_state.custom_dict[source]
                st.rerun()
else:
    st.info("词典为空")



# Add information about OpenCC
st.markdown("""
<div style="text-align: center; opacity: 0.8; font-size: 0.9rem; margin-top: 2rem; padding: 1rem;">
    <p>基于 <a href="https://github.com/BYVoid/OpenCC" target="_blank">OpenCC</a> 开发 | 
    支持简体、繁体、台湾繁体、香港繁体和日文新字体之间的转换</p>
</div>
""", unsafe_allow_html=True)
