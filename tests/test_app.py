import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from opencc_converter import CustomOpenCC


class AppTests(unittest.TestCase):
    def make_app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()

    def test_default_conversion_other_direction_and_clear(self):
        app = self.make_app()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, '规范汉字繁简转换工具')
        self.assertEqual(app.caption[0].value, '基于openCC与《通用规范汉字表》的中文简繁转换工具，支持自定义词典功能。')
        self.assertEqual(app.selectbox(key='source_language').value, '简体')
        self.assertEqual(app.selectbox(key='target_language').value, '规范繁体')
        app.text_area(key='input_text').set_value('两晋异体字，绿色记录').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '兩晋异體字，緑色記録')
        app.selectbox(key='target_language').set_value('台湾繁体').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, CustomOpenCC('s2tw').convert('两晋异体字，绿色记录'))
        # Changing the source to the previously selected target must choose a valid target.
        app.selectbox(key='source_language').set_value('台湾繁体').run()
        self.assertEqual(app.selectbox(key='target_language').value, '简体')
        app.selectbox(key='target_language').set_value('规范繁体').run()
        app.text_area(key='input_text').set_value('綠色記錄').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '緑色記録')
        app.selectbox(key='resource').set_value('繁体→规范繁体 · 词库').run()
        self.assertEqual(len(app.get('download_button')), 4)
        app.button(key='clear_text_btn').click().run()
        self.assertEqual(app.text_area(key='input_text').value, '')
        self.assertEqual(app.text_area(key='output_text').value, '')
        self.assertEqual(len(app.exception), 0)

    def test_every_visible_pair_is_distinct_and_supported(self):
        app = self.make_app()
        text = '綠色记录，皇后以后读书。'
        for source in app.selectbox(key='source_language').options:
            app.selectbox(key='source_language').set_value(source).run()
            self.assertNotIn(source, app.selectbox(key='target_language').options)
            for target in app.selectbox(key='target_language').options:
                with self.subTest(source=source, target=target):
                    app.selectbox(key='target_language').set_value(target).run()
                    app.text_area(key='input_text').set_value(text).run()
                    app.button(key='convert_text_btn').click().run()
                    self.assertEqual(len(app.exception), 0)
                    self.assertEqual(app.text_area(key='output_text').value,
                                     CustomOpenCC(app.session_state.scheme).convert(text))
                    self.assertTrue(any('文本和上传的文档均使用当前选择。' in m.value for m in app.markdown))

    def test_swap_and_mixed_input(self):
        app = self.make_app()
        self.assertEqual([tab.label for tab in app.tabs], ['文档转换', '文本转换'])
        app.text_area(key='input_text').set_value('侷限、羣、批註、两、悅悦').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '局限、群、批注、兩、悦悦')
        app.button(key='swap_languages').click().run()
        self.assertEqual(app.selectbox(key='source_language').value, '规范繁体')
        self.assertEqual(app.selectbox(key='target_language').value, '简体')
        self.assertEqual(app.text_area(key='output_text').value, '')
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '局限、群、批注、两、悦悦')
        app.button(key='swap_languages').click().run()
        self.assertEqual(app.selectbox(key='source_language').value, '简体')
        self.assertEqual(app.selectbox(key='target_language').value, '规范繁体')
        app.selectbox(key='source_language').set_value('其他繁体').run()
        self.assertTrue(app.button(key='swap_languages').disabled)
        self.assertEqual(len(app.exception), 0)


if __name__ == '__main__':
    unittest.main()
