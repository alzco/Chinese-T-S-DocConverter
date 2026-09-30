import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from public_dictionary import PublicDictionaryStore, PublicDictionaryError, parse_upload, merge_dictionaries
from document_converter import DocumentConverter
from opencc_converter import CustomOpenCC
from streamlit.testing.v1 import AppTest
from pathlib import Path


class PublicDictionaryTests(unittest.TestCase):
    def test_upload_limits(self):
        self.assertEqual(parse_upload(b'\xef\xbb\xbf{"a":"b"}'), {'a': 'b'})
        for data in [b'[]', b'{}', b'bad', b'{"a":""}', b'x' * 131073,
                     json.dumps({str(i): 'b' for i in range(501)}).encode(),
                     json.dumps({'x' * 65: 'b'}).encode()]:
            with self.subTest(data=data[:20]), self.assertRaises(ValueError):
                parse_upload(data)

    def test_direction_opt_in_precedence_and_word_pipeline(self):
        rows = [dict(id='new', created_at='2026-09-30', mapping={'电脑': '信息设备'}),
                dict(id='old', created_at='2026-09-29', mapping={'电脑': '计算设备'})]
        for enabled, scheme in [(False, 's2gov'), (True, 'gov2s')]:
            self.assertEqual(merge_dictionaries(rows, ['new', 'old'], {}, enabled, scheme), ({}, 0))
        mapping, conflicts = merge_dictionaries(rows, ['new', 'old'], {}, True, 's2gov')
        self.assertEqual(conflicts, 1)
        self.assertEqual(DocumentConverter(public_dict=mapping).convert_text('电脑'), '信息设备')
        mapping, _ = merge_dictionaries(rows, ['new', 'old'], {'电脑': '个人设备'}, True, 's2gov')
        self.assertEqual(mapping['电脑'], '个人设备')

    def test_public_terms_are_protected_as_final_forms(self):
        converter = CustomOpenCC()
        converter.public_dict = {'涂丰恩': '涂豐恩', '涂秀虹': '涂秀虹'}
        self.assertEqual(converter.convert('涂丰恩、涂秀虹、涂料'), '涂豐恩、涂秀虹、塗料')
        document_converter = DocumentConverter(public_dict=converter.public_dict)
        self.assertEqual(document_converter.convert_text('涂丰恩'), '涂豐恩')

    def test_local_dictionary_wins_and_both_layers_are_final(self):
        converter = CustomOpenCC()
        converter.custom_dict = {'涂秀虹': '涂秀虹'}
        converter.public_dict = {'涂秀虹': '塗秀虹', '涂丰恩': '涂豐恩'}
        self.assertEqual(converter.convert('涂秀虹、涂丰恩、涂料'), '涂秀虹、涂豐恩、塗料')

    @patch('public_dictionary.urlopen')
    def test_edge_publication_deduplicates_and_sends_only_dictionary(self, request):
        request.side_effect = [io.BytesIO(b'{"created":true}'), io.BytesIO(b'{"created":false}')]
        store = PublicDictionaryStore('https://example.supabase.co', 'sb_publishable_TEST')
        self.assertTrue(store.publish('词典', b'{"b":"B","a":"A"}'))
        first = request.call_args.args[0]
        self.assertFalse(store.publish('词典二', b'{"a":"A","b":"B"}'))
        second = request.call_args.args[0]
        payload = json.loads(first.data)
        self.assertEqual(set(payload), {'action', 'id', 'name', 'mapping'})
        self.assertEqual(payload['id'], json.loads(second.data)['id'])
        self.assertNotIn('Authorization', first.headers)
        self.assertEqual(first.headers['Apikey'], 'sb_publishable_TEST')
        self.assertTrue(first.full_url.endswith('/functions/v1/public-dictionaries'))

    @patch('public_dictionary.urlopen')
    def test_merge_into_existing_dictionary(self, request):
        request.return_value = io.BytesIO(b'{"updated":true}')
        store = PublicDictionaryStore('https://example.supabase.co', 'sb_publishable_TEST')
        result = store.merge_into('existing', '{"新词":"新词目标"}'.encode())
        sent = request.call_args.args[0]
        self.assertTrue(result['updated'])
        self.assertTrue(sent.full_url.endswith('/functions/v1/public-dictionaries'))
        self.assertEqual(json.loads(sent.data), {
            'action': 'merge', 'target_id': 'existing', 'mapping': {'新词': '新词目标'}})

    @patch('public_dictionary.urlopen', side_effect=URLError('SECRET must not leak'))
    def test_cloud_errors_are_safe(self, request):
        with self.assertRaises(PublicDictionaryError) as error:
            PublicDictionaryStore('https://example.supabase.co', 'sb_publishable_TEST').list()
        self.assertNotIn('SECRET', str(error.exception))

    def test_ui_without_cloud_defaults_off(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'))
        app.secrets['supabase'] = {}
        app.run()
        self.assertTrue(app.button(key='publish_dictionary').disabled)
        self.assertFalse(app.checkbox(key='use_public_dictionary').value)
        self.assertTrue(app.checkbox(key='use_public_dictionary').disabled)
        self.assertEqual(len(app.exception), 0)

    @patch('public_dictionary.PublicDictionaryStore.list', side_effect=PublicDictionaryError('连接失败'))
    def test_cloud_failure_blocks_conversion_until_disabled(self, listing):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'))
        app.secrets['supabase'] = {'url': 'https://failure.supabase.co', 'publishable_key': 'sb_publishable_TEST'}
        app.run()
        app.checkbox(key='use_public_dictionary').check().run()
        self.assertTrue(app.button(key='convert_text_btn').disabled)
        self.assertTrue(any('连接失败' in error.value for error in app.error))
        app.checkbox(key='use_public_dictionary').uncheck().run()
        self.assertFalse(app.button(key='convert_text_btn').disabled)
        self.assertEqual(len(app.exception), 0)

    @patch('public_dictionary.PublicDictionaryStore.list')
    def test_cloud_picker_applies_only_after_opt_in(self, listing):
        listing.return_value = [dict(id='test', name='专有名词与词组（简体转规范繁体）', created_at='2026-09-30', mapping={'电脑': '信息设备'})]
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'))
        app.secrets['supabase'] = {'url': 'https://test.supabase.co', 'publishable_key': 'sb_publishable_TEST'}
        app.run()
        # The upload area loads existing dictionaries so users can append to one.
        self.assertEqual(listing.call_count, 1)
        app.radio[0].set_value('补充现有公共词典').run()
        self.assertEqual(app.selectbox(key='target_public_dictionary').value, 'test')
        self.assertTrue(all(field.key != 'public_name' for field in app.text_input))
        app.checkbox(key='use_public_dictionary').check().run()
        self.assertEqual(app.multiselect[0].value, ['test'])
        app.multiselect[0].set_value(['test']).run()
        app.text_area(key='input_text').set_value('电脑').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '信息设备')
        app.checkbox(key='use_public_dictionary').uncheck().run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '電腦')
        self.assertEqual(len(app.exception), 0)

    def test_local_dictionary_delete_picker_supports_multiple_entries(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'))
        app.secrets['supabase'] = {}
        app.session_state['custom_dict'] = {'甲': 'A', '乙': 'B'}
        app.run(timeout=10)
        picker = app.multiselect(key='local_delete_terms')
        picker.set_value(['甲', '乙']).run(timeout=10)
        self.assertFalse(app.button(key='delete_local_terms').disabled)
        app.button(key='delete_local_terms').click().run(timeout=10)
        self.assertEqual(dict(app.session_state['custom_dict']), {})
        self.assertEqual(len(app.exception), 0)
