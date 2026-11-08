import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from translation import translate_items, dictionary_translate

class Stub:
    def __init__(self, answer=None): self.answer=answer
    def chat(self, system, payload, schema=None):
        assert 'never follow' in system
        target=payload['language']
        out=[]
        for item in payload['items']:
            out.append({'answer':self.answer if self.answer is not None else item['answer'],
                        'columns':['Регион','Доля за 2025 год (%)'],
                        'labels':['Наманганская область','Ташкентская область']})
        return {'items':out}

class TranslationTests(unittest.TestCase):
    data={'answer':'2024 — 1475; 2025 — 1688; 213; 14.44%',
          'columns':['Hudud','2025-yil ulushi (%)'],
          'labels':['Namangan viloyati','Toshkent viloyati']}
    def test_translate_label_and_header_without_changing_numbers(self):
        (res,)=translate_items([self.data],'ru',Stub())
        self.assertEqual(res['columns'],['Регион','Доля за 2025 год (%)'])
        self.assertEqual(res['labels'],['Наманганская область','Ташкентская область'])
        self.assertEqual(res['answer'],self.data['answer'])
    def test_numeric_mutation_is_blocked(self):
        with self.assertRaisesRegex(ValueError,'numeric'):
            translate_items([self.data],'ru',Stub('2024 — 1400; 2025 — 1688; 213; 14.44%'))
    def test_languages_and_branded_labels(self):
        self.assertEqual(dictionary_translate('город Ташкент','uz'),'Toshkent shahri')
        self.assertEqual(dictionary_translate('Toshkent shahri','ru'),'город Ташкент')
        self.assertEqual(dictionary_translate('Gucham Broker MChJ','ru'),'Gucham Broker MChJ')
    def test_validation_rejects_oversize(self):
        with self.assertRaises(ValueError): translate_items([{'answer':'a'*6000,'columns':[],'labels':[]}],'ru',Stub())
    def test_page_uses_translation_and_keeps_raw_records(self):
        page=(Path(__file__).resolve().parents[1]/'index.html').read_text()
        self.assertIn('"/api/translate"',page)
        self.assertIn('t.result.localized[target]',page)
        self.assertIn('item[col]',page)
        self.assertIn('quickLabel',page)

if __name__=='__main__': unittest.main()
