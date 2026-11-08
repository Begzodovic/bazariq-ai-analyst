import json
import threading
import unittest
import urllib.request
from unittest.mock import Mock, patch
from analyst import Analyst
from app import ROOT, make_server
from database import Register


class GreetingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.register = Register(ROOT / "uzex.db")

    def test_uzbek_greetings_do_not_call_gemini(self):
        provider = Mock()
        agent = Analyst(self.register, provider)
        for question in ("salom", "Salom!", "Assalomu alaykum", "Rahmat"):
            with self.subTest(question=question):
                result = agent.ask(question)
                self.assertEqual(result["status"], "chat")
                self.assertEqual(result["lang"], "uz")
                self.assertEqual(result["rows"], [])
        provider.chat.assert_not_called()

    def test_russian_greetings_do_not_call_gemini(self):
        provider = Mock()
        agent = Analyst(self.register, provider)
        for question in ("Привет", "Здравствуйте!", "Спасибо"):
            result = agent.ask(question)
            self.assertEqual(result["status"], "chat")
            self.assertEqual(result["lang"], "ru")
        provider.chat.assert_not_called()

    def test_real_data_questions_not_swallowed(self):
        from analyst import smalltalk_reply
        for question in ("Salom, 2025-yilda nechta bitim bo'lgan?", "Привет, кто топ-5 брокеров?", "2025-yil bitimlari"):
            self.assertIsNone(smalltalk_reply(question))

    def test_http_endpoint_returns_200_without_model(self):
        provider = Mock()
        provider.name = 'Gemini'
        provider.model = 'test'
        provider.key = 'fake'
        provider.verified = False
        with patch.dict('os.environ', {'BAZARIQ_PUBLIC':'1'}):
            server = make_server(self.register, provider, 0)
            worker = threading.Thread(target=server.serve_forever,daemon=True)
            worker.start()
            try:
                payload = json.dumps({'question':'salom', 'lang':'uz'}).encode()
                req = urllib.request.Request('http://127.0.0.1:%d/api/ask' % server.server_port,
                    data=payload, headers={'Content-Type':'application/json'},method='POST')
                with urllib.request.urlopen(req,timeout=5) as response:
                    self.assertEqual(response.status,200)
                    body=json.loads(response.read())
                    self.assertEqual(body['status'],'chat')
            finally:
                server.shutdown()
                server.server_close()
        provider.chat.assert_not_called()

if __name__ == '__main__': unittest.main()
