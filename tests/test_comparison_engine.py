import unittest
from analyst import apply_requested_format, comparison_analysis

class ComparisonEngineTests(unittest.TestCase):
    def test_one_row_two_named_counts(self):
        r={'status':'ok','lang':'uz','rows':[{'toshkent_count':21247,'namangan_count':13580}], 'truncated':False}
        q='Toshkent shahri va Namangan viloyatidagi bitimlar farqini va Namanganga nisbatan foizni hisobla. Formulalarni ko‘rsat. Jadval tuzma.'
        a=apply_requested_format(r,q)
        self.assertEqual(a['display_format'],'text')
        for t in ('21 247','13 580','7 667','56,46%','÷','Xulosa:'):
            self.assertIn(t,a['answer'])
        self.assertNotIn('|',a['answer'])

    def test_two_rows_labeled_comparison(self):
        r={'status':'ok','lang':'uz','rows':[{'Hudud':'Toshkent shahri','Bitimlar soni':21247}, {'Hudud':'Namangan viloyati','Bitimlar soni':13580}], 'truncated':False}
        q='Toshkent shahri va Namangan viloyatini solishtir. Namangan viloyatiga nisbatan necha foiz farq bor? Jadval tuzma.'
        self.assertIn('56,46%',apply_requested_format(r,q)['answer'])

    def test_year_on_year_russian(self):
        r={'status':'ok','lang':'ru','rows':[{'deals_2024':21247,'deals_2025':24478}], 'truncated':False}
        q='Сравни количество сделок в 2024 и 2025 году. Рассчитай абсолютную разницу и процент изменения в 2025 относительно 2024. Только текстом, без таблицы.'
        a=apply_requested_format(r,q)
        self.assertIn('3 231',a['answer'])
        self.assertIn('15,21%',a['answer'])
        self.assertIn('Вывод:',a['answer'])

    def test_year_on_year_reverse_columns(self):
        r={'status':'ok','lang':'ru','rows':[{'2025_count':24478,'2024_count':21247}], 'truncated':False}
        q='Сравни 2024 и 2025. Какой процент изменения? Только текстом.'
        self.assertIn('15,21%',apply_requested_format(r,q)['answer'])

    def test_unrelated_numeric_columns_do_not_invent(self):
        r={'status':'ok','lang':'uz','rows':[{'income':21247,'expense':13580}], 'truncated':False}
        self.assertIsNone(comparison_analysis(r,'uz','farq va foizni hisobla'))

    def test_ambiguous_baseline_does_not_guess(self):
        r={'status':'ok','lang':'uz','rows':[{'toshkent_count':21247,'namangan_count':13580}], 'truncated':False}
        self.assertIsNone(comparison_analysis(r,'uz','Toshkent va Namangan foiz farqi nechta?'))

    def test_truncated_refuses_derived(self):
        r={'status':'ok','lang':'uz','rows':[{'toshkent_count':21247,'namangan_count':13580}], 'truncated':True}
        self.assertIsNone(comparison_analysis(r,'uz','Namanganga nisbatan Toshkent farqi necha foiz?'))

    def test_zero_denominator(self):
        r={'status':'ok','lang':'uz','rows':[{'toshkent_count':12,'namangan_count':0}], 'truncated':False}
        a=comparison_analysis(r,'uz','Toshkent va Namanganga nisbatan foiz farqi?')
        self.assertIn('hisoblab bo‘lmaydi',a)

    def test_do_not_overwrite_fixed_sql_answer(self):
        r={'status':'ok','lang':'uz','rows':[{'Hudud':'Toshkent shahri','Bitimlar soni':21247},{'Hudud':'Namangan viloyati','Bitimlar soni':13580}], 'truncated':False, 'ai_status':'not_needed','answer':'Tasdiqlangan farq: 7667; formula: 21247-13580.'}
        q='Toshkent shahri Namanganga nisbatan farqni hisobla. Jadval tuzma.'
        a=apply_requested_format(r,q)
        self.assertEqual(a['answer'],r['answer'])

if __name__ == '__main__': unittest.main()
