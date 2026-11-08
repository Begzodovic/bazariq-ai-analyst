import unittest
from unittest.mock import Mock
from analyst import Analyst, smalltalk_reply
from app import friendly_failure

class LocalePriorityTests(unittest.TestCase):
    def test_ru_ui_russian_reply_for_uzbek_smalltalk(self):
        a=Analyst.__new__(Analyst)
        result=a._ask_once('Salom', 'ru', [])
        self.assertEqual(result['lang'],'ru')
        self.assertIn('Здравствуйте',result['answer'])

    def test_uz_ui_uzbek_reply_for_russian_smalltalk(self):
        a=Analyst.__new__(Analyst)
        result=a._ask_once('Спасибо', 'uz', [])
        self.assertEqual(result['lang'],'uz')
        self.assertIn('Marhamat',result['answer'])

    def test_ru_unavailable_localized_even_when_model_returns_uz(self):
        a=Analyst.__new__(Analyst)
        a.db=Mock()
        a.provider=Mock()
        a.provider.chat.return_value={'status':'unavailable', 'lang':'uz','reason':'insufficient'}
        a.fast_mode=False
        a._catalog=lambda q:{}
        result=a._ask_once('Brokerlarning maoshi qancha?', 'ru', [])
        self.assertEqual(result['lang'],'ru')
        self.assertIn('недостаточно',result['answer'].lower())

    def test_uz_unavailable_localized_even_when_model_returns_ru(self):
        a=Analyst.__new__(Analyst)
        a.db=Mock()
        a.provider=Mock()
        a.provider.chat.return_value={'status':'unavailable', 'lang':'ru','reason':'insufficient'}
        a.fast_mode=False
        a._catalog=lambda q:{}
        result=a._ask_once('Сколько получают брокеры?', 'uz', [])
        self.assertEqual(result['lang'],'uz')
        self.assertIn('yetarli',result['answer'])

    def test_error_translations(self):
        self.assertIn('Попробуйте',friendly_failure(422,'ru'))
        self.assertIn('Yangi chatda',friendly_failure(422,'uz'))

if __name__=='__main__': unittest.main()
