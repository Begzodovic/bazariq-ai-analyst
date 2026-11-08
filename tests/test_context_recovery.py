import unittest
from unittest.mock import patch
from analyst import Analyst, independent_question

class ContextRecoveryTests(unittest.TestCase):
    def test_independent_question_resets_old_state(self):
        q='Какие 5 регионов Узбекистана заключили больше всего сделок за 2024 год?'
        self.assertTrue(independent_question(q))
        agent=Analyst.__new__(Analyst)
        with patch.object(agent, '_ask_once', return_value={'status':'ok'}) as call:
            agent.ask(q, 'ru', [{'question':'2025 yilda Toshkent bitimlari','state':{'years':['2025']}}])
        self.assertEqual(call.call_args.args[2], [])
    def test_followup_keeps_selected_ids(self):
        q='Endi aynan shu 5 ta brokerning Toshkentdagi ishtiroklarini hisobla.'
        self.assertFalse(independent_question(q))
        agent=Analyst.__new__(Analyst)
        old=[{'question':'TOP 5 broker','selected_set':['101','102']}]
        with patch.object(agent, '_ask_once', return_value={'status':'ok'}) as call:
            agent.ask(q,'uz',old)
        self.assertEqual(call.call_args.args[2][0]['selected_set'], ['101','102'])
    def test_error_suggests_new_chat_only_with_prior(self):
        agent=Analyst.__new__(Analyst)
        with patch.object(agent, '_ask_once', return_value={'status':'error','diagnostic':'period'}):
            x=agent.ask('Shu 5 ta brokerning hisobi','uz',[{'question':'TOP 5 broker'}])
            self.assertTrue(x['suggest_new_chat'])
            y=agent.ask('2024-yilda TOP-5 hudud','uz',[])
            self.assertNotIn('suggest_new_chat',y)
if __name__=='__main__':unittest.main()
