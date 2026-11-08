import json
import os
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from analyst import Analyst, AUDIT
from app import ROOT, make_server
from database import QueryError, Register, fold
from provider import Provider, ProviderError, load_env


class Scripted:
    """Test double for model transport only. SQL still runs on the real SQLite file."""
    def __init__(self, *decisions):
        self.decisions=iter(decisions)
        self.calls=[]

    def chat(self, system,payload, *, schema=None):
        self.calls.append((system,payload.copy()))
        return next(self.decisions)


def candidate(sql,lang="uz"):
    return {"status":"query","sql":sql,"method":"Davr bo‘yicha satrlar sanaldi.","lang":lang}


ACCEPT={"verdict":"accept","check_sql":"SELECT count(id) FROM deals WHERE substr(day,1,4)='2025'"}
YEAR="SELECT count(*) AS bitimlar_soni FROM deals WHERE day >= '2025-01-01' AND day < '2026-01-01'"


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=Register(ROOT/"uzex.db")

    def test_actual_register(self):
        self.assertEqual(self.db.context["deal_date_coverage"],("2022-01-03","2026-10-30"))
        self.assertEqual(self.db.execute("SELECT count(*) n FROM deals")["rows"],[{"n":500000}])
        self.assertEqual(self.db.execute(YEAR)["rows"],[{"bitimlar_soni":115763}])

    def test_prohibited(self):
        for sql in ["DELETE FROM deals","WITH a AS (SELECT 1) DELETE FROM deals",
                    "SELECT * FROM deals; DELETE FROM deals","SELECT * FROM sqlite_schema",
                    "SELECT * FROM pragma_table_info('deals')","SELECT load_extension('x') FROM deals",
                    "ATTACH 'x' AS db","SELECT randomblob(100000) FROM deals","SELECT no_such FROM deals",
                    'SELECT "no_such" FROM deals',"SELECT 115763","SELECT * FROM imaginary"]:
            with self.subTest(sql=sql),self.assertRaises(QueryError):
                self.db.execute(sql)

    def test_file_readonly(self):
        with closing(self.db.connect()) as conn,self.assertRaises(sqlite3.OperationalError):
            conn.execute("DELETE FROM deals WHERE 0")

    def test_timeout(self):
        with self.assertRaisesRegex(QueryError,"interrupted"):
            self.db.execute("SELECT sum(a.id*b.id) FROM deals a, deals b",seconds=.002)

    def test_rank_and_sources(self):
        r=self.db.execute("""WITH counts AS (SELECT p.region, count(*) AS n FROM deals d
            JOIN participants p ON p.inn=d.buyer_inn GROUP BY p.region)
            SELECT region,dense_rank() OVER(ORDER BY n DESC) AS pos FROM counts ORDER BY pos""",row_limit=3)
        self.assertEqual(r["source"],["deals","participants"])
        self.assertEqual(len(r["rows"]),3)
        self.assertTrue(r["truncated"])
        self.assertEqual(r["rows"][0]["pos"],1)

    def test_null_zero_empty_distinct(self):
        for sql,expect in [("SELECT avg(amount) n FROM deals WHERE id=-1","yetarli"),
                           ("SELECT count(*) n FROM deals WHERE id=-1","n: 0"),
                           ("SELECT id FROM deals WHERE id=-1","topilmadi")]:
            a=Analyst(self.db,Scripted(candidate(sql),{"verdict":"accept","check_sql":sql}))
            self.assertIn(expect,a.ask("Sinov")["answer"])

    def test_single_statement_literals(self):
        r=self.db.execute("SELECT 'a;b' AS txt FROM brokers LIMIT 1;")
        self.assertEqual(r["rows"],[{"txt":"a;b"}])

    def test_casefold(self):
        self.assertEqual(fold("FARG‘ONA"),fold("Farg'ona"))
        self.assertEqual(fold("ЁЛКА"),"елка")

    def test_ignored_year_repaired_before_audit(self):
        p=Scripted(candidate("SELECT count(*) FROM deals"),candidate(YEAR),ACCEPT)
        r=Analyst(self.db,p).ask("2025-yilda nechta bitim bo‘lgan?")
        self.assertEqual(r["repairs"],1)
        self.assertEqual(r["rows"],[{"bitimlar_soni":115763}])
        self.assertEqual(p.calls[-1][0],AUDIT)

    def test_scalar_disagreement_rejected(self):
        wrong={"verdict":"accept","check_sql":"SELECT count(id)+1 FROM deals WHERE substr(day,1,4)='2025'"}
        p=Scripted(candidate(YEAR),wrong,candidate(YEAR),ACCEPT)
        r=Analyst(self.db,p).ask("2025-yilda nechta bitim bor?")
        self.assertEqual(r["repairs"],1)
        self.assertIn("disagrees",p.calls[2][1]["history"][0]["reason"])
        self.assertEqual(r["check_sql"],ACCEPT["check_sql"])

    def test_sql_repair(self):
        p=Scripted(candidate("SELECT no_such FROM deals"),candidate(YEAR),ACCEPT)
        r=Analyst(self.db,p).ask("Сколько сделок за 2025 год?")
        self.assertIn("no such column",p.calls[1][1]["history"][0]["reason"])
        self.assertEqual(r["repairs"],1)

    def test_audit_rejection_bounded(self):
        pair=[candidate("SELECT count(*) FROM deals"),{"verdict":"repair","issue":"Role filter missing."}]
        p=Scripted(*(pair*3))
        r=Analyst(self.db,p).ask("Xaridor tomonidagi bitimlarni sanang")
        self.assertEqual(r["status"],"error")
        self.assertEqual(r["rows"],[])
        self.assertEqual(len(p.calls),6)

    def test_lookup_then_clarify(self):
        p=Scripted({"status":"lookup","sql":"SELECT DISTINCT region FROM deals ORDER BY region LIMIT 5"},
                   {"status":"clarify","message":"Город или область?","lang":"ru"})
        r=Analyst(self.db,p).ask("Сделки Ташкента?")
        self.assertEqual(r["status"],"clarify")
        self.assertTrue(p.calls[-1][1]["history"][0]["rows"])

    def test_unavailable(self):
        p=Scripted({"status":"unavailable","message":"Нет сведений о прибыли.","lang":"ru"})
        self.assertEqual(Analyst(self.db,p).ask("Прибыль?")["sql"],"")

    def test_false_claim_in_abstention_is_not_displayed(self):
        p=Scripted({"status":"unavailable","lang":"uz","message":"Invented buyer and value 9999999."})
        r=Analyst(self.db,p).ask("Xaridorning pasport raqami?")
        self.assertEqual((r["status"],r["rows"],r["sql"]),("unavailable",[],""))
        self.assertNotIn("9999999",r["answer"])

    def test_literal_cannot_pass_as_a_database_fact(self):
        fake="SELECT 123456 AS amount FROM deals LIMIT 1"
        with self.assertRaises(QueryError):
            self.db.execute(fake, analytical=True)
        p=Scripted(*[candidate(fake)]*3)
        r=Analyst(self.db,p).ask("Qancha?")
        self.assertEqual((r["status"],r["rows"]),("error",[]))
        self.assertNotIn("123456",r["error"])

    def test_outside_coverage_count_abstains(self):
        sql="SELECT count(*) n FROM deals WHERE day >= '2030-01-01' AND day < '2031-01-01'"
        r=Analyst(self.db,Scripted(candidate(sql))).ask("2030-yilda nechta bitim qayd etilgan?")
        self.assertEqual((r["status"],r["rows"]),("unavailable",[]))
        self.assertIn("2026-10-30",r["answer"])

    def test_followup_context_is_used_by_planner_and_reviewer(self):
        turns=[{"question":"2025-yilda bitimlar soni?","reply":"Uydirma javob 9999999."}]
        p=Scripted(candidate(YEAR),ACCEPT)
        r=Analyst(self.db,p).ask("Shu davrdagi sonni yana tekshir",conversation=turns)
        self.assertEqual(r["rows"],[{"bitimlar_soni":115763}])
        for _,payload in p.calls:
            self.assertEqual(payload["conversation"],turns)

    def test_clarification_uses_safe_field_and_language(self):
        p=Scripted({"status":"clarify","field":"metric","lang":"ru","message":"Invented result 999."})
        r=Analyst(self.db,p).ask("Какой брокер лучший?")
        self.assertIn("показатель",r["answer"])
        self.assertNotIn("999",r["answer"])

    def test_fibre_clarification_uses_only_real_product_labels(self):
        p=Scripted({"status":"clarify","lang":"uz","field":"entity","product_codes":["520100","fake","520512"]})
        r=Analyst(self.db,p).ask("2025-yilda paxta tolasi bo‘yicha nechta bitim qayd etilgan?")
        self.assertEqual(r["status"],"clarify")
        self.assertIn("520100",r["answer"])
        self.assertIn("520512",r["answer"])
        self.assertNotIn("fake",r["answer"])
        self.assertEqual(r["rows"],[])

    def test_check_sql_requested_without_replanning_product_query(self):
        sql="""SELECT COUNT(*) AS bitimlar_soni FROM deals d JOIN contracts c ON c.id=d.contract_id
               WHERE d.day >= '2025-01-01' AND d.day < '2026-01-01' AND c.hs_code='520100'"""
        verify="""SELECT COUNT(id) FROM deals WHERE substr(day,1,4)='2025' AND contract_id IN
                  (SELECT id FROM contracts WHERE replace(fold(product),'-',' ') LIKE 'хлопок сырец%')"""
        p=Scripted(candidate(sql),{"verdict":"accept"},{"verdict":"accept","check_sql":verify})
        r=Analyst(self.db,p).ask("2025-yilda paxta xomashyosi bo‘yicha nechta bitim bor?")
        self.assertEqual(r["rows"],[{"bitimlar_soni":33056}])
        self.assertEqual(p.calls[1][0],AUDIT)
        self.assertEqual(p.calls[2][0],AUDIT)
        self.assertEqual(r["repairs"],0)

    def test_failure_reports_the_sql_stage_without_an_answer(self):
        p=Scripted(*[candidate("SELECT missing_column FROM deals")]*3)
        r=Analyst(self.db,p).ask("Tekshiring")
        self.assertEqual((r["status"],r["diagnostic"],r["rows"]),("error","sql",[]))

    def test_latest_rate_with_sql_only_or_missing_method(self):
        sql = "SELECT day AS sana,rate AS kurs FROM usd_rates ORDER BY day DESC LIMIT 1"
        for partial in [{"sql":sql},{"status":" QUERY ","query":sql}]:
            model=Scripted(partial,{"verdict":"accept"})
            r=Analyst(self.db,model).ask("Reyestrdagi eng oxirgi USD kursi qaysi sanaga tegishli va necha so‘m?")
            self.assertEqual(r["rows"],[{"sana":"2026-10-31","kurs":13357.84}])
            self.assertEqual(r["source"],["usd_rates"])
            self.assertEqual(r["repairs"],0)
            self.assertEqual(model.calls[-1][0],AUDIT)

    def test_answer_object_does_not_bypass_planning(self):
        invalid={"answer":"invented","sql":"SELECT rate FROM usd_rates LIMIT 1"}
        r=Analyst(self.db,Scripted(invalid,invalid,invalid)).ask("Последний курс?")
        self.assertEqual((r["status"],r["diagnostic"],r["rows"]),("error","plan",[]))

    def test_invalid_input(self):
        for q in [None,""," ","?"*1501]:
            with self.assertRaises(ValueError): Analyst(self.db,Scripted()).ask(q)


class ProviderTests(unittest.TestCase):
    def test_gemini_latest_rate_bypasses_provider(self):
        with patch.dict(os.environ,{"AI_PROVIDER":"gemini","GEMINI_MODEL":"test","GEMINI_API_KEY":"test"},clear=True):
            p=Provider()
            with patch.object(p,"request",side_effect=AssertionError("Network call on exact rate lookup")):
                result=Analyst(Register(ROOT/"uzex.db"),p).ask("На какую дату приходится последний курс USD и сколько он составляет?")
        self.assertEqual(result["lang"],"ru")
        self.assertEqual(result["rows"],[{"дата":"2026-10-31","курс_usd_uzs":13357.84}])

    def test_fast_broker_list_complete(self):
        with patch.dict(os.environ,{"AI_PROVIDER":"groq","GROQ_MODEL":"test","GROQ_API_KEY":"test"},clear=True):
            p=Provider()
            with patch.object(p,"chat",side_effect=AssertionError("Unexpected AI")):
                a=Analyst(Register(ROOT/"uzex.db"),p)
                result=a.ask("Brokerlar ro‘yxatini ber")
                self.assertEqual(len(result["rows"]),120)
                self.assertFalse(result["truncated"])
                self.assertEqual(a.ask("Brokerlar ro‘yxatini ber")["rows"],result["rows"])

    def test_env_does_not_override_process(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{"AI_PROVIDER":"xai"},clear=True):
            Path(d,".env").write_text('AI_PROVIDER=groq\nGEMINI_MODEL="abc"')
            load_env(d)
            self.assertEqual((Provider().id,Provider().model),("gemini","abc"))

    def test_model_error_has_actual_provider_and_no_secret(self):
        for provider,prefix,label in [("gemini","GEMINI","Google Gemini")]:
            env={"AI_PROVIDER":provider,prefix+"_MODEL":"missing",prefix+"_API_KEY":"private-token"}
            with patch.dict(os.environ,env,clear=True),patch("urllib.request.OpenerDirector.open",
                    side_effect=urllib.error.HTTPError("https://api.invalid",404,"private-token",{},None)):
                with self.assertRaises(ProviderError) as ctx:
                    Provider().check()
                self.assertIn(label,str(ctx.exception))
                self.assertIn("404",str(ctx.exception))
                self.assertNotIn("private-token",str(ctx.exception))

    def test_bad_json_and_model_check(self):
        with patch.dict(os.environ,{"GEMINI_API_KEY":"secret","GEMINI_MODEL":"test"},clear=True):
            p=Provider()
            for raw in ["not JSON",'{"ok":false}']:
                with patch.object(p,"request",return_value={"choices":[{"message":{"content":raw}}]}),self.assertRaises(ProviderError):
                    p.check()
            with patch.object(p,"request",return_value={"choices":[{"message":{"content":'{"ok":true}'}}]}):
                self.assertEqual(p.check(),"test")
                self.assertTrue(p.verified)

    def test_http_result_and_sources(self):
        with patch.dict(os.environ,{},clear=True):
            p=Provider()
            with patch.object(p,"chat",side_effect=[candidate(YEAR),ACCEPT]):
                with make_server(Register(ROOT/"uzex.db"),p,0) as server:
                    thread=threading.Thread(target=server.serve_forever,daemon=True)
                    thread.start()
                    try:
                        base=f"http://127.0.0.1:{server.server_port}"
                        with urllib.request.urlopen(base) as page:
                            self.assertIn("BazarIQ",page.read().decode())
                        request=urllib.request.Request(base+"/api/ask",
                            data=json.dumps({"question":"2025-yilda nechta bitim?"}).encode(),
                            headers={"Content-Type":"application/json"})
                        with urllib.request.urlopen(request) as res:
                            r=json.load(res)
                        self.assertEqual(r["source"],["deals"])
                        self.assertEqual(r["answer"],"So‘ralgan shartlar bo‘yicha 115 763 ta bitim qayd etilgan.")
                        self.assertNotIn("check_sql",r)  # FAST: no second model call
                    finally:
                        server.shutdown()
                        thread.join()

    def test_no_fallback_via_http(self):
        with patch.dict(os.environ,{},clear=True):
            with make_server(Register(ROOT/"uzex.db"),Provider(),0) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                try:
                    base=f"http://127.0.0.1:{server.server_port}"
                    with urllib.request.urlopen(base+"/health") as response:
                        h=json.load(response)
                        self.assertFalse(h["configured"])
                        self.assertFalse(h["verified"])
                    req=urllib.request.Request(base+"/api/ask",data=json.dumps({"question":"2025-yilda nechta bitim?"}).encode(),
                                               headers={"Content-Type":"application/json"})
                    with self.assertRaises(urllib.error.HTTPError) as ctx: urllib.request.urlopen(req)
                    self.assertEqual(ctx.exception.code,503)
                    body=json.load(ctx.exception)
                    self.assertEqual(body["rows"],[])
                    self.assertIn("Google Gemini",body["error"])
                finally:
                    server.shutdown()
                    thread.join()


if __name__=="__main__":
    unittest.main()
