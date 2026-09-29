import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from opencc_converter import CustomOpenCC


class AppTests(unittest.TestCase):
    def test_default_conversion_other_scheme_and_clear(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.selectbox(key='scheme').value, 's2gov')
        self.assertEqual(len(app.checkbox), 0)
        app.text_area(key='input_text').set_value('两晋异体字，绿色记录').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '兩晋异體字，緑色記録')
        app.selectbox(key='scheme').set_value('s2t').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, CustomOpenCC('s2t').convert('两晋异体字，绿色记录'))
        app.selectbox(key='scheme').set_value('t2gov').run()
        app.text_area(key='input_text').set_value('綠色記錄').run()
        app.button(key='convert_text_btn').click().run()
        self.assertEqual(app.text_area(key='output_text').value, '緑色記録')
        app.selectbox(key='resource').set_value('繁体→规范繁体 · 词库').run()
        self.assertEqual(len(app.get('download_button')), 4)
        app.button(key='clear_text_btn').click().run()
        self.assertEqual(app.text_area(key='input_text').value, '')
        self.assertEqual(app.text_area(key='output_text').value, '')
        self.assertEqual(len(app.exception), 0)


if __name__ == '__main__':
    unittest.main()
