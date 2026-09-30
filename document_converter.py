#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Document Converter Module
Handles conversion of text in various document formats (txt, md, docx)
using OpenCC for Chinese character conversion.
"""

import io
import re
from zipfile import ZipFile
from difflib import SequenceMatcher
from lxml import etree
from opencc_converter import CustomOpenCC

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{' + W_NS + '}'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

class DocumentConverter:
    """
    A class for converting text in various document formats using OpenCC.
    Supports txt, md, and docx files.
    """
    
    def __init__(self, opencc_config='s2gov', custom_dict=None, public_dict=None):
        """
        Initialize the document converter.
        
        Args:
            opencc_config (str): The OpenCC configuration to use
            custom_dict (dict): Optional custom dictionary for conversion
        """
        self.converter = CustomOpenCC(opencc_config)
        self.converter.public_dict = dict(public_dict or {})
        
        # Add custom dictionary entries if provided
        if custom_dict:
            for source, target in custom_dict.items():
                self.converter.add_custom_mapping(source, target)
    
    def convert_text(self, text):
        """
        Convert plain text using OpenCC.
        
        Args:
            text (str): The text to convert
            
        Returns:
            str: The converted text
        """
        return self.converter.convert(text)
    
    def convert_txt_file(self, file_content):
        """
        Convert a text file.
        
        Args:
            file_content (bytes): The content of the text file
            
        Returns:
            str: The converted text
        """
        try:
            text = file_content.decode('utf-8')
            return self.convert_text(text)
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                text = file_content.decode('gbk')
                return self.convert_text(text)
            except:
                raise ValueError("无法解码文本文件，请确保文件编码为UTF-8或GBK")
    
    def convert_md_file(self, file_content):
        """
        Convert a Markdown file.
        
        Args:
            file_content (bytes): The content of the Markdown file
            
        Returns:
            str: The converted Markdown text
        """
        # Markdown files are treated the same as text files
        return self.convert_txt_file(file_content)
    
    def convert_docx_file(self, file_content):
        """Convert Word text parts in memory, retaining XML formatting and package parts."""
        output = io.BytesIO()
        with ZipFile(io.BytesIO(file_content)) as source, ZipFile(output, 'w') as target:
            target.comment = source.comment
            for item in source.infolist():
                data = source.read(item.filename)
                if re.fullmatch(r'word/(document|footnotes|endnotes|header[^/]*|footer[^/]*)\.xml', item.filename):
                    parser = etree.XMLParser(resolve_entities=False, no_network=True)
                    root = etree.fromstring(data, parser)
                    for paragraph in root.iter(W + 'p'):
                        if not any(parent.tag in {W + 'del', W + 'moveFrom'} for parent in paragraph.iterancestors()):
                            self._convert_xml_paragraph(paragraph)
                    data = etree.tostring(root, encoding='UTF-8', xml_declaration=True)
                target.writestr(item, data)
        return output.getvalue()

    def _convert_xml_paragraph(self, paragraph):
        # Work across formatting runs and hyperlinks, but never across paragraphs,
        # tabs, line breaks, fields or deleted text. Nested text boxes are handled
        # by their own paragraph, so each text node is converted exactly once.
        nodes = []

        def flush():
            if nodes:
                self._convert_text_nodes(nodes)
                nodes.clear()

        def visit(element):
            for child in element:
                if child.tag in {W + 'p', W + 'del', W + 'moveFrom'}:
                    flush()
                elif child.tag in {W + 'tab', W + 'br', W + 'cr', W + 'fldChar', W + 'instrText'}:
                    flush()
                elif child.tag == W + 't':
                    nodes.append(child)
                else:
                    visit(child)

        visit(paragraph)
        flush()

    def _convert_text_nodes(self, nodes):
        original = ''.join(node.text or '' for node in nodes)
        converted = self.convert_text(original)
        if original == converted:
            return
        # Most conversions preserve length; this keeps every run's exact range.
        # For custom phrases that change length, map boundaries through the diff
        # instead of collapsing all text into the first formatted run.
        boundaries = [0]
        for node in nodes:
            boundaries.append(boundaries[-1] + len(node.text or ''))
        if len(original) == len(converted):
            mapped = boundaries
        else:
            opcodes = SequenceMatcher(None, original, converted, autojunk=False).get_opcodes()
            mapped = []
            for boundary in boundaries:
                position = len(converted)
                for _, start, end, new_start, new_end in opcodes:
                    if start <= boundary <= end:
                        position = (new_start + (boundary - start) * (new_end - new_start) // (end - start)
                                    if end > start else new_end)
                        break
                mapped.append(position)
            mapped[0], mapped[-1] = 0, len(converted)
        for node, start, end in zip(nodes, mapped, mapped[1:]):
            node.text = converted[start:end]
            if node.text and (node.text[0].isspace() or node.text[-1].isspace()):
                node.set(XML_SPACE, 'preserve')

    def convert_file(self, file_content, file_type):
        """
        Convert a file based on its type.
        
        Args:
            file_content (bytes): The content of the file
            file_type (str): The type of the file ('txt', 'md', or 'docx')
            
        Returns:
            Union[str, bytes]: The converted content (str for txt/md, bytes for docx)
        """
        if file_type == 'txt':
            return self.convert_txt_file(file_content)
        elif file_type == 'md':
            return self.convert_md_file(file_content)
        elif file_type == 'docx':
            return self.convert_docx_file(file_content)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
