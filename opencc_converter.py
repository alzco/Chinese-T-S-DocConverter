"""OpenCC conversion with vendored Tonggui configurations and custom mappings."""
import json
from functools import lru_cache
from pathlib import Path

from opencc import OpenCC

DATA_DIR = Path(__file__).resolve().parent / 'vendor' / 'tonggui'
UPSTREAM_CONFIGS = {
    's2gov': 's2t.json',
    't2gov': 't2gov.json',
    'gov2s': 't2s.json',
    't2new': 't2new.json',
    't2gov_keep_simp': 't2gov_keep_simp.json',
    't2new_keep_simp': 't2new_keep_simp.json',
}
STANDARD_CONFIGS = ('s2t', 't2s', 's2tw', 'tw2s', 's2hk', 'hk2s', 's2twp',
                    'tw2sp', 't2tw', 'hk2t', 't2hk', 't2jp', 'jp2t', 'tw2t')


@lru_cache(maxsize=24)
def get_engine(config):
    if config in UPSTREAM_CONFIGS:
        return OpenCC(str(DATA_DIR / UPSTREAM_CONFIGS[config]))
    if config not in STANDARD_CONFIGS:
        raise ValueError(f'不支持的转换方案：{config}')
    return OpenCC(config)


def validate_dictionary(mapping):
    if not isinstance(mapping, dict) or any(
        not isinstance(k, str) or not k or not isinstance(v, str)
        for k, v in mapping.items()
    ):
        raise ValueError('词典须为 JSON 对象，键为非空字符串，值为字符串。')
    return dict(mapping)


class CustomOpenCC:
    def __init__(self, config='s2gov'):
        self.config = config
        self.converter = get_engine(config)
        self.custom_dict = {}

    def convert(self, text):
        # Retain the original app's pre-conversion custom dictionary behavior.
        for source, target in self.custom_dict.items():
            text = text.replace(source, target)
        return self.converter.convert(text)

    def add_custom_mapping(self, source, target):
        self.custom_dict.update(validate_dictionary({source: target}))

    def remove_custom_mapping(self, source):
        self.custom_dict.pop(source, None)

    def load_custom_dict(self, dict_path):
        try:
            with open(dict_path, encoding='utf-8') as file:
                self.custom_dict = validate_dictionary(json.load(file))
            return True
        except (OSError, ValueError):
            return False

    def save_custom_dict(self, dict_path):
        try:
            with open(dict_path, 'w', encoding='utf-8') as file:
                json.dump(self.custom_dict, file, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    def get_available_configs(self):
        return list(UPSTREAM_CONFIGS) + list(STANDARD_CONFIGS)
