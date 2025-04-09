#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenCC Converter with Custom Dictionary Support
This script provides functionality for simplified-traditional Chinese conversion
with support for custom dictionaries.
"""

import os
import json
from opencc import OpenCC
import tempfile
import shutil

class CustomOpenCC:
    """
    A wrapper around OpenCC that allows for custom dictionary support.
    """
    
    def __init__(self, config='s2t'):
        """
        Initialize the converter with a specific configuration.
        
        Args:
            config (str): The conversion configuration to use (e.g., 's2t', 't2s', etc.)
        """
        self.config = config
        self.converter = OpenCC(config)
        self.custom_dict = {}
        
    def convert(self, text):
        """
        Convert text using OpenCC with custom dictionary applied.
        
        Args:
            text (str): The text to convert
            
        Returns:
            str: The converted text
        """
        # First apply the custom dictionary
        for k, v in self.custom_dict.items():
            text = text.replace(k, v)
            
        # Then apply the standard OpenCC conversion
        return self.converter.convert(text)
    
    def add_custom_mapping(self, source, target):
        """
        Add a custom mapping from source to target.
        
        Args:
            source (str): The source text
            target (str): The target text to convert to
        """
        self.custom_dict[source] = target
    
    def remove_custom_mapping(self, source):
        """
        Remove a custom mapping.
        
        Args:
            source (str): The source text to remove from custom dictionary
        """
        if source in self.custom_dict:
            del self.custom_dict[source]
    
    def load_custom_dict(self, dict_path):
        """
        Load a custom dictionary from a JSON file.
        
        Args:
            dict_path (str): Path to the JSON dictionary file
        """
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                self.custom_dict = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading custom dictionary: {e}")
            return False
    
    def save_custom_dict(self, dict_path):
        """
        Save the current custom dictionary to a JSON file.
        
        Args:
            dict_path (str): Path to save the JSON dictionary file
        """
        try:
            with open(dict_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving custom dictionary: {e}")
            return False
    
    def get_available_configs(self):
        """
        Get a list of available conversion configurations.
        
        Returns:
            list: List of available configurations
        """
        return [
            's2t',    # Simplified to Traditional
            't2s',    # Traditional to Simplified
            's2tw',   # Simplified to Traditional (Taiwan Standard)
            'tw2s',   # Traditional (Taiwan Standard) to Simplified
            's2hk',   # Simplified to Traditional (Hong Kong variant)
            'hk2s',   # Traditional (Hong Kong variant) to Simplified
            's2twp',  # Simplified to Traditional (Taiwan Standard) with Taiwanese idiom
            'tw2sp',  # Traditional (Taiwan Standard) to Simplified with Mainland Chinese idiom
            't2tw',   # Traditional to Taiwan Standard
            'hk2t',   # Traditional (Hong Kong variant) to Traditional
            't2hk',   # Traditional to Hong Kong variant
            't2jp',   # Traditional to New Japanese Kanji
            'jp2t',   # New Japanese Kanji to Traditional
            'tw2t'    # Traditional (Taiwan standard) to Traditional
        ]

# Example usage
if __name__ == "__main__":
    # Create a converter with s2t (Simplified to Traditional) configuration
    converter = CustomOpenCC('s2t')
    
    # Add some custom mappings
    converter.add_custom_mapping("计算机", "電腦")
    converter.add_custom_mapping("软件", "軟體")
    
    # Test conversion
    simplified_text = "这是一个计算机软件。"
    traditional_text = converter.convert(simplified_text)
    
    print(f"Original: {simplified_text}")
    print(f"Converted: {traditional_text}")
    
    # Save custom dictionary
    converter.save_custom_dict("custom_dict.json")
    
    # Create a new converter and load the dictionary
    new_converter = CustomOpenCC('s2t')
    new_converter.load_custom_dict("custom_dict.json")
    
    # Test the new converter
    new_traditional_text = new_converter.convert(simplified_text)
    print(f"Converted with loaded dictionary: {new_traditional_text}")
