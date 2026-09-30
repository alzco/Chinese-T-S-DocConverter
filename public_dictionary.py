"""Server-side Supabase storage; no documents or conversion text are uploaded."""
import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from opencc_converter import validate_dictionary

MAX_BYTES = 128 * 1024
MAX_ENTRIES = 500


class PublicDictionaryError(Exception):
    pass


def parse_upload(data):
    if len(data) > MAX_BYTES:
        raise ValueError('词典不能超过 128 KB。')
    try:
        mapping = validate_dictionary(json.loads(data.decode('utf-8-sig')))
    except (UnicodeError, ValueError) as error:
        raise ValueError('请上传 JSON 对象，例如 {"原词": "替换词"}。') from error
    if not mapping or len(mapping) > MAX_ENTRIES:
        raise ValueError('词典须包含 1–500 个词条。')
    if any(len(k) > 64 or len(v) > 256 or not v.strip() or not k.strip() for k, v in mapping.items()):
        raise ValueError('原词最多 64 字，替换词最多 256 字，均不能为空。')
    return mapping


def merge_dictionaries(records, selected_ids, personal, enabled, scheme):
    merged = {}
    conflicts = set()
    if enabled and scheme == 's2gov':
        # Stable order: the picker order does not change precedence.
        for record in sorted(records, key=lambda row: (row['created_at'], row['id'])):
            if record['id'] in selected_ids:
                for source, target in record['mapping'].items():
                    if source in merged and merged[source] != target:
                        conflicts.add(source)
                    merged[source] = target
    merged.update(personal)
    return merged, len(conflicts)


def select_public_dictionary(records, selected_ids, enabled, scheme):
    """Return only selected public entries for protected final-form replacement."""
    merged, conflicts = merge_dictionaries(records, selected_ids, {}, enabled, scheme)
    return merged, conflicts


class PublicDictionaryStore:
    def __init__(self, url, key):
        parts = urlparse(url)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.query or parts.fragment:
            raise PublicDictionaryError('公共词典连接配置无效。')
        self.project_url = url.rstrip('/')
        self.api_root = self.project_url + '/rest/v1'
        self.url = self.api_root + '/public_dictionaries'
        self.function_url = self.project_url + '/functions/v1/public-dictionaries'
        self.key = key

    def _request(self, method, suffix='', payload=None):
        headers = {'apikey': self.key, 'Content-Type': 'application/json'}
        request = Request(self.url + suffix, method=method, headers=headers,
                          data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode())
        try:
            with urlopen(request, timeout=10) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            # Never surface response bodies, credentials or connection details to users.
            raise PublicDictionaryError('公共词典暂时无法连接，请稍后重试。') from error

    def list(self):
        rows = self._request('GET', '?select=id,name,mapping,created_at&active=eq.true&order=created_at.desc,id.asc&limit=100')
        try:
            for row in rows:
                row['mapping'] = parse_upload(json.dumps(row['mapping'], ensure_ascii=False).encode())
                for field in ('id', 'name', 'created_at'):
                    if not isinstance(row[field], str):
                        raise ValueError('Invalid row')
            return rows
        except (TypeError, KeyError, ValueError) as error:
            raise PublicDictionaryError('公共词典数据格式异常，请联系维护者。') from error

    def publish(self, name, data):
        name = name.strip()
        if not 1 <= len(name) <= 60:
            raise ValueError('请填写 1–60 字的词典名称。')
        mapping = parse_upload(data)
        canonical = json.dumps(mapping, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        payload = {'action': 'publish', 'id': hashlib.sha256(canonical).hexdigest(),
                   'name': name, 'mapping': mapping}
        return bool(self._submit(payload).get('created'))

    def merge_into(self, dictionary_id, data):
        """Atomically add entries to an existing dictionary; new values win."""
        mapping = parse_upload(data)
        result = self._submit({'action': 'merge', 'target_id': dictionary_id,
                               'mapping': mapping})
        if not result.get('updated'):
            raise PublicDictionaryError('没有找到要更新的公共词典。')
        return result

    def _submit(self, payload):
        """Send anonymous contributions through the server-side Edge Function."""
        request = Request(self.function_url, method='POST',
                          headers={'apikey': self.key, 'Content-Type': 'application/json'},
                          data=json.dumps(payload, ensure_ascii=False).encode())
        try:
            with urlopen(request, timeout=10) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            raise PublicDictionaryError('公共词典暂时无法更新，请稍后重试。') from error
