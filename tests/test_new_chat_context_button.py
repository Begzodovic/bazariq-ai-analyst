import pathlib
import unittest
from unittest.mock import patch
from analyst import Analyst

class NewChatContextButtonTests(unittest.TestCase):
    def setUp(self):
        self.agent=object.__new__(Analyst)
        self.prior=[{'question':'2024-yilda eng faol 5 brokerni ko‘rsat','selected_set':['11','22']}]

    def test_only_dependent_failure_suggests_new_chat(self):
        with patch.object(Analyst,'_ask_once',return_value={'status':'error','error':'failed'}):
            result=self.agent.ask('Endi shu 5 ta brokerning ishtiroklarini hisobla','uz',self.prior)
        self.assertTrue(result.get('suggest_new_chat'))

    def test_independent_failure_does_not_suggest_new_chat(self):
        with patch.object(Analyst,'_ask_once',return_value={'status':'error','error':'failed'}):
            result=self.agent.ask('2024-yilda eng ko‘p bitim bo‘lgan 5 hududni ko‘rsat','uz',self.prior)
        self.assertFalse(result.get('suggest_new_chat',False))

    def test_no_prior_failure_does_not_suggest_new_chat(self):
        with patch.object(Analyst,'_ask_once',return_value={'status':'error','error':'failed'}):
            result=self.agent.ask('Endi shu 5 ta brokerni solishtir','uz',[])
        self.assertFalse(result.get('suggest_new_chat',False))

    def test_button_uses_original_error_question(self):
        page=(pathlib.Path(__file__).resolve().parents[1]/'index.html').read_text()
        self.assertIn('renderReply(turn.result,turn.done,turn.question,active)',page)
        self.assertIn('prepareFreshQuestion(originalQuestion||"",sourceChat)',page)
        self.assertNotIn('const last=active.turns[active.turns.length-1];',page)

if __name__=='__main__': unittest.main()
