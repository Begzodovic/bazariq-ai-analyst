import unittest
from unittest.mock import patch
from analyst import Analyst,requested_format,prose_summary,apply_requested_format

class OutputFormatTests(unittest.TestCase):
    def test_uz_no_table_wins(self):
        q='2024-yilda holatni tahlil qil, jadval tuzma, faqat matn shaklida javob ber.'
        self.assertEqual(requested_format(q),'text')
    def test_ru_no_table(self):
        self.assertEqual(requested_format('Ответь без таблицы, только текстом'),'text')
    def test_explicit_table(self):
        self.assertEqual(requested_format('Natijani jadvalda ko‘rsat'),'table')
    def test_no_fabricated_statistics(self):
        x={'status':'ok','lang':'uz','rows':[{'Holat':'Исполнен','Bitimlar soni':80},{'Holat':'Аннулирован','Bitimlar soni':20}], 'truncated':False}
        r=apply_requested_format(x, 'Jadval tuzma, faqat matn shaklida holatni ayt')
        self.assertEqual(r['display_format'],'text')
        self.assertIn('80',r['answer'])
        self.assertIn('20',r['answer'])
        self.assertNotIn('|',r['answer'])
        self.assertIn('80.00%',r['answer'])
    def test_zero_or_empty(self):
        x={'status':'ok','lang':'uz','rows':[]}
        self.assertIn('natija topilmadi',apply_requested_format(x,'jadval tuzma')['answer'])
    def test_works_for_fast_paths_and_ai(self):
        agent=Analyst.__new__(Analyst)
        r={'status':'ok','lang':'uz','rows':[{'Holat':'Исполнен','Bitimlar soni':2},{'Holat':'Bekor','Bitimlar soni':1}]}
        with patch.object(agent,'_ask_once',return_value=r):
            x=agent.ask('2024-yilda bitimlar holati. Jadval tuzma, faqat matn shaklida izohla','uz',[])
        self.assertEqual(x['display_format'],'text')
        self.assertIn('Исполнен',x['answer'])
        self.assertIn('Bekor',x['answer'])

if __name__=='__main__': unittest.main()
