import unittest
from unittest.mock import Mock
from app import ROOT
from database import Register
from analyst import Analyst

QUESTION=('Среди этих пяти регионов сравни количество биржевых сделок в Ташкенте (город) '
          'и Наманганской области за 2024 год. На сколько сделок больше было заключено '
          'в Ташкенте и на сколько процентов количество сделок в Ташкенте превышает '
          'показатель Наманганской области? Покажи формулу расчёта и ответь на русском языке.')

class RegionCompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=Register(ROOT/'uzex.db')
    def test_exact_followup_no_llm(self):
        model=Mock()
        agent=Analyst(self.db,model)
        earlier={'question':'Какие 5 регионов заключили больше всего сделок за 2024 год?',
                 'reply':'г. Ташкент, Наманганская область и другие','prior_sql':'SELECT region FROM deals LIMIT 5',
                 'state':{'years':['2024'],'metric':'deal_count'}}
        r=agent.ask(QUESTION,'ru',[earlier])
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['lang'],'ru')
        self.assertIn('7,667', r['answer'])
        self.assertIn('56,46%', r['answer'])
        self.assertIn("2024-01-01",r['sql'])
        self.assertIn("2025-01-01",r['sql'])
        self.assertEqual([x['Количество сделок'] for x in r['rows']],[21247,13580])
        model.chat.assert_not_called()
    def test_dont_hijack_ambiguous_city(self):
        from fastpath import compare_tashkent_namangan
        self.assertIsNone(compare_tashkent_namangan(self.db,'Сравни Наманган и Ташкент за 2024 год', 'ru'))
    def test_uzbek_comparison(self):
        from fastpath import compare_tashkent_namangan
        r=compare_tashkent_namangan(self.db,'2024-yilda Toshkent shahri va Namangan viloyati bitimlarini taqqosla','uz')
        self.assertEqual(r['status'],'ok')
        self.assertIn('7667',r['answer'].replace(',',''))

if __name__=='__main__': unittest.main()
