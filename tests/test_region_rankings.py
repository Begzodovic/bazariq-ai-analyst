import unittest
from unittest.mock import Mock
from app import ROOT
from analyst import Analyst
from database import Register

class RegionRankingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=Register(ROOT/'uzex.db')

    def test_2024_russian_region_ranking_no_llm(self):
        llm=Mock()
        agent=Analyst(self.db,llm)
        q=('Какие 5 регионов Узбекистана заключили наибольшее количество биржевых '
           'сделок за 2024 год? Для каждого региона укажи количество сделок, '
           'общую сумму торгов в узбекских сумах и процентную долю от общего '
           'количества сделок по всей республике. Отсортируй по убыванию количества сделок.')
        result=agent.ask(q, 'ru')
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['lang'],'ru')
        self.assertEqual(len(result['rows']),5)
        self.assertIn('2024-01-01',result['sql'])
        self.assertIn('2025-01-01',result['sql'])
        self.assertEqual(result['rows'][0]['Количество сделок'],21247)
        self.assertEqual(result['rows'][0]['Регион'],'Toshkent shahri')
        self.assertEqual(result['rows'][0]['Доля по республике (%)'],19.92)
        self.assertTrue(all(a['Количество сделок'] >= b['Количество сделок'] for a,b in zip(result['rows'],result['rows'][1:])))
        llm.chat.assert_not_called()

    def test_no_hijack_seller_region(self):
        from fastpath import region_top_five
        q='Топ-5 регионов регистрации продавцов по сделкам в 2024 году с долей и суммой'
        self.assertIsNone(region_top_five(self.db,q,'ru'))

if __name__=='__main__': unittest.main()
