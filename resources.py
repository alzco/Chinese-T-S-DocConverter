"""Attribution and downloadable, reproducible upstream resources."""
import io
import json
from functools import lru_cache
from zipfile import ZipFile, ZIP_DEFLATED
from opencc_converter import DATA_DIR

SOURCE = json.loads((DATA_DIR / 'SOURCE.json').read_text(encoding='utf-8'))
UPSTREAM_URL = SOURCE['repository']
TABLE_SOURCE_URL = 'https://www.moe.gov.cn/jyb_sjzl/ziliao/A19/201306/t20130601_186002.html'
TABLE_PDF_URL = 'https://www.gov.cn/gzdt/att/att/site1/20130819/tygfhzb.pdf'
DOWNLOADS = {
    '简体→规范繁体 · 字表': 'STCharacters.txt',
    '简体→规范繁体 · 词库': 'STPhrases.txt',
    '繁体→规范繁体 · 字表': 'TGCharacters.txt',
    '繁体→规范繁体 · 词库': 'TGPhrases.txt',
    '繁体→简体 · 字表': 'TSCharacters.txt',
    '繁体→简体 · 词库': 'TSPhrases.txt',
    '旧字形→新字形 · 字表': 'GovVariants.txt',
    '相容汉字正规化 · 字表': 'CJK_Compatibility_Ideographs.txt',
    '繁体规范化（保留简体）· 字表': 'TGCharacters_keep_simp.txt',
    '旧字形转新字形（保留简体）· 字表': 'GovVariants_keep_simp.txt',
}


@lru_cache(maxsize=1)
def dictionary_bundle():
    output = io.BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as bundle:
        for path in sorted(DATA_DIR.iterdir()):
            if path.is_file():
                bundle.writestr('tonggui/' + path.name, path.read_bytes())
    return output.getvalue()
