import os
import threading
import unittest
import urllib.request
from unittest.mock import Mock, patch
from app import make_server, ROOT
from database import Register

class PublicDeployTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = Register(ROOT / 'uzex.db')
        provider = Mock(name='provider')
        provider.name='Google Gemini'
        provider.model='gemini-3.1-flash-lite'
        provider.key='fake-not-real'
        provider.verified=False
        cls.public_patch=patch.dict(os.environ,{'BAZARIQ_PUBLIC':'1','BAZARIQ_BASIC_USER':'old','BAZARIQ_BASIC_PASSWORD':'old'})
        cls.public_patch.start()
        cls.server=make_server(reg,provider,0)
        cls.worker=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.worker.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.public_patch.stop()
    def test_home_public_even_with_legacy_password_env(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.server.server_port}/') as r:
            self.assertEqual(r.status,200)
            self.assertIn(b'html',r.read().lower())
    def test_health_public(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.server.server_port}/health') as r:
            self.assertEqual(r.status,200)
    def test_packaged_database(self):
        self.assertEqual(len(list(ROOT.glob('uzex.db.gz.part*'))), 4)
        self.assertFalse((ROOT / 'uzex.db').exists())
