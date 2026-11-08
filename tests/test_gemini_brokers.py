"""Regression test: the exact jury broker follow-up must preserve chosen codes."""
import unittest
from pathlib import Path
from unittest.mock import Mock
from analyst import Analyst
from database import Register

ROOT=Path(__file__).resolve().parents[1]
QUESTION='Endi aynan shu 5 ta brokerning 2025-yilda Toshkent shahrida tuzilgan bitimlardagi sotuvchi va xaridor ishtiroklarini hisobla. Jami ishtiroklarni ham ko‘rsat. Yangi TOP-5 tanlama.'

class BrokerFollowupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=Register(ROOT/'uzex.db')

    def test_pinned_broker_codes_and_region(self):
        provider=Mock(id='gemini',name='Google Gemini',model='test')
        a=Analyst(self.db,provider)
        codes=['BK001','BK002','BK003','BK004','BK005']
        result=a.ask(QUESTION,conversation=[{'question':'TOP-5 brokerlar','selected_set':codes}])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['selected_set'],codes)
        self.assertEqual([row['broker_code'] for row in result['rows']],codes)
        self.assertIn("fold(region) = 'toshkent shahri'",result['sql'])
        self.assertNotIn('toshkent viloyati',result['sql'])
        self.assertTrue(all(row['sotuvchi_ishtirok']+row['xaridor_ishtirok']==row['jami_ishtirok'] for row in result['rows']))
        provider.chat.assert_not_called()

    def test_legacy_chats_recover_names_by_sql(self):
        a=Analyst(self.db,Mock(id='gemini', name='Google Gemini',model='test'))
        old="SELECT name AS broker_nomi FROM brokers WHERE code IN ('BK001','BK002','BK003','BK004','BK005') ORDER BY code"
        result=a.ask(QUESTION,conversation=[{'question':'TOP-5 brokerlar','prior_sql':old}])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['selected_set'],['BK001','BK002','BK003','BK004','BK005'])

    def test_missing_prior_selection_not_invented(self):
        a=Analyst(self.db,Mock(id='gemini',name='Google Gemini',model='test'))
        result=a._broker_followup(QUESTION,[{'question':'Brokerlar top 5'}],'uz')
        self.assertIsNone(result)

if __name__=='__main__':unittest.main()
