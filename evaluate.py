"""Held-out bilingual cases. Never imported by the application. Python oracles cross-check SQL."""
import argparse
import json
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from analyst import Analyst
from database import Register
from provider import Provider, ProviderError, load_env

ROOT = Path(__file__).resolve().parent


@dataclass
class Case:
    kind: str
    uz: str
    ru: str
    sql: str = ""
    expected: tuple = ()
    status: str = "ok"


def cases(db, seed):
    rng = random.Random(seed)
    year = rng.choice([2023,2024,2025])
    month = rng.randrange(1,12)
    start, end = f"{year}-{month:02}-01", f"{year}-{month+1:02}-01"
    window = f"day >= '{start}' AND day < '{end}'"
    # Sample actual domain values rather than encoding example answers.
    vals = db.context["values"]
    region = rng.choice(vals["deals.region"])
    def lit(s):
        return "'" + s.replace("'","''") + "'"
    reg = lit(region)
    n = rng.choice([3,4,5])
    with closing(db.connect()) as conn:
        contracts = dict(conn.execute("SELECT id,currency FROM contracts"))
        rates = dict(conn.execute("SELECT day,rate FROM usd_rates"))
        companies = dict(conn.execute("SELECT inn,region FROM participants"))
        broker_names = dict(conn.execute("SELECT code,name FROM brokers"))
        broker = rng.choice(sorted(broker_names))
        dates, counts, regional, volumes, amounts, broker_counts = Counter(), Counter(), Counter(), [], [], Counter()
        partial, late, joined, filtered = 0,0,0,0
        participants = defaultdict(set)
        query = """SELECT day,status,region,unit,quantity,lot,amount,contract_id,seller_inn,buyer_inn,
                          buyer_broker,seller_broker,delivery_day,payment_day FROM deals"""
        for day,status,wh,unit,qty,lot,amount,cid,seller,buyer,bb,sb,delivery,payment in conn.execute(query):
            dates[day[:4]] += 1
            if not start <= day < end:
                continue
            counts[status] += 1
            regional[wh] += 1
            if status == "Исполнен" and wh == region:
                filtered += 1
            if wh == region and companies[buyer] != wh:
                joined += 1
            participants[buyer].add(seller)
            broker_counts[bb] += 1
            if bb == broker or sb == broker:
                partial += 1
            if unit == "тонна" and contracts[cid] == "Узбекский сум":
                volumes.append(qty * lot)
                amounts.append(amount)
            if delivery and payment and delivery < payment:
                late += 1
        usd_total = 0.
        for day,amt,cid in conn.execute("SELECT day,amount,contract_id FROM deals WHERE day>=? AND day<? ORDER BY id",(start,end)):
            usd_total += amt * rates[day] if contracts[cid]=="Доллар США" else amt
    period_u = f"{start} dan {end} gacha (oxirgi sana kirmaydi)"
    period_r = f"с {start} до {end} (не включая конечную дату)"
    def one(value):
        return ((value,),)
    def top(counter, bottom=False):
        return tuple(sorted(counter.items(), key=lambda x:(x[1] if bottom else -x[1],x[0]))[:n])
    y0, y1 = dates[str(year-1)], dates[str(year)]
    return [
        Case("year",f"{year}-yilda reyestrda nechta bitim qayd etilgan?",f"Сколько сделок в реестре за {year} год?",
             f"SELECT count(*) FROM deals WHERE day >= '{year}-01-01' AND day < '{year+1}-01-01'",one(y1)),
        Case("multi_filter",f"{period_u} sotuvchi ombori «{region}» bo‘lgan to‘liq bajarilgan bitimlar soni?",
             f"Сколько полностью исполненных сделок {period_r}, если регион склада продавца — «{region}»?",
             f"SELECT count(*) FROM deals WHERE {window} AND region={reg} AND status='Исполнен'",one(filtered)),
        Case("buyer_warehouse",f"{period_u} ombori «{region}»da, xaridorning ro‘yxatdagi hududi esa boshqa bo‘lgan bitimlardan nechta bor?",
             f"Сколько сделок {period_r} со складом в «{region}», где покупатель зарегистрирован в другом регионе?",
             f"SELECT count(*) FROM deals d JOIN participants p ON p.inn=d.buyer_inn WHERE {window} AND d.region={reg} AND p.region<>d.region",one(joined)),
        Case("top",f"{period_u} bitim soni eng ko‘p {n} ta ombor hududi va sonini chiqaring. Teng bo‘lsa hudud nomi o‘sish tartibida.",
             f"Назови {n} регионов склада с наибольшим количеством сделок {period_r} и их количество. При равенстве сортируй по названию.",
             f"SELECT region,count(*) n FROM deals WHERE {window} GROUP BY region ORDER BY n DESC,region LIMIT {n}",top(regional)),
        Case("bottom",f"{period_u} xaridor tomonida qatnashgan brokerlardan bitimi eng kam {n} tasining kodi va bitim soni? Teng bo‘lsa kodi bo‘yicha o‘sish tartibida.",
             f"Из брокеров, работавших на стороне покупателя {period_r}, выведи {n} с наименьшим числом сделок: код и число. При равенстве упорядочь по коду.",
             f"SELECT buyer_broker,count(*) n FROM deals WHERE {window} GROUP BY buyer_broker ORDER BY n,buyer_broker LIMIT {n}",top(broker_counts,True)),
        Case("both_roles",f"{period_u} {broker} broker xaridor yoki sotuvchi tomonida qatnashgan noyob bitimlar soni?",
             f"В скольких отдельных сделках {period_r} участвовал брокер {broker} хотя бы на одной стороне?",
             f"SELECT count(*) FROM deals WHERE {window} AND (buyer_broker='{broker}' OR seller_broker='{broker}')",one(partial)),
        Case("converted",f"{period_u} barcha holatlardagi bitimlar summasi jami necha so‘m? USDni bitim kunidagi kursda aylantiring. Faqat jami, ikki kasr xonasigacha.",
             f"Чему равна сумма всех сделок {period_r} в сумах, включая все статусы, USD по курсу дня сделки? Только итог с округлением до сотых.",
             f"""SELECT round(sum(CASE c.currency WHEN 'Доллар США' THEN d.amount*r.rate ELSE d.amount END),2)
                 FROM deals d JOIN contracts c ON c.id=d.contract_id JOIN usd_rates r ON r.day=d.day
                 WHERE d.day >= '{start}' AND d.day < '{end}'""",one(round(usd_total,2))),
        Case("weighted",f"{period_u} valyutasi so‘m, birligi tonna bo‘lgan bitimlarda hajm bo‘yicha vaznlangan narx qancha? So‘m/tonna, ikki kasr xonasigacha.",
             f"Какова средневзвешенная по объёму цена в сумах за тонну {period_r}, только для сумовых контрактов с единицей «тонна»? Округли до сотых.",
             f"""SELECT round(sum(d.amount)/nullif(sum(d.quantity*d.lot),0),2) FROM deals d
                 JOIN contracts c ON c.id=d.contract_id WHERE {window} AND d.unit='тонна' AND c.currency='Узбекский сум'""",
             one(round(sum(amounts)/sum(volumes),2) if sum(volumes) else None)),
        Case("yoy",f"{year}-yilda bitimlar soni {year-1}-yildagiga qaraganda necha foiz o‘zgardi? Faqat foiz, ikki kasr xonasigacha.",
             f"На сколько процентов изменилось число сделок за {year} год относительно {year-1} года? Только процент, округли до сотых.",
             f"""WITH y AS (SELECT substr(day,1,4) yr,count(*) n FROM deals GROUP BY 1)
                 SELECT round(100.0*(b.n-a.n)/nullif(a.n,0),2) FROM y a,y b WHERE a.yr='{year-1}' AND b.yr='{year}'""",
             one(round((y1-y0)*100/y0,2))),
        Case("nested",f"{period_u} kamida uch xil sotuvchi bilan bitim tuzgan xaridorlar soni qancha?",
             f"Сколько покупателей заключили сделки как минимум с тремя разными продавцами {period_r}?",
             f"SELECT count(*) FROM (SELECT buyer_inn FROM deals WHERE {window} GROUP BY buyer_inn HAVING count(DISTINCT seller_inn)>=3)",
             one(sum(len(x)>=3 for x in participants.values()))),
        Case("empty",f"{period_u} yetkazish sanasi to‘lov sanasidan oldin bo‘lgan bitimlar soni?",f"Сколько сделок {period_r} с датой поставки раньше даты оплаты?",
             f"SELECT count(*) FROM deals WHERE {window} AND delivery_day < payment_day",one(late)),
        Case("clarify","Eng yaxshi brokerni ayting.","Какой брокер лучший?",status="clarify"),
        Case("missing","Xaridorlarning sof foydasi jami qancha?","Какова суммарная чистая прибыль покупателей?",status="unavailable"),
        Case("coverage","2039-yildagi haqiqiy savdo aylanmasi qancha?","Каков фактический оборот в 2039 году?",status="unavailable"),
    ]


def values(result):
    return tuple(tuple(row[c] for c in result["columns"]) for row in result["rows"])


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    parser.add_argument("--seed",type=int,default=714)
    parser.add_argument("--limit",type=int,help="maximum number of case pairs")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    load_env(ROOT)
    db=Register(ROOT/"uzex.db")
    suite=cases(db,args.seed)
    if args.limit is not None:
        if args.limit<1: parser.error("limit >= 1")
        suite=suite[:args.limit]
    logs=[]
    for c in suite:
        if c.sql:
            actual=values(db.execute(c.sql))
            if actual!=c.expected:
                raise AssertionError((c.kind,actual,c.expected))
        logs.append({"kind":c.kind,"oracle":c.expected,"reference_sql":c.sql,"expected_status":c.status})
    report={"seed":args.seed,"mode":"reference","verified_reference_queries":sum(bool(c.sql) for c in suite),"cases":logs}
    if args.live:
        p=Provider()
        p.check()
        agent=Analyst(db,p)
        runs=[]
        for c in suite:
            for lang in ("uz","ru"):
                before=time.perf_counter()
                try:
                    r=agent.ask(getattr(c,lang),lang)
                except ProviderError as exc:
                    r={"status":"provider_error","error":str(exc)}
                executed=r.get("status")=="ok"
                rows=values(r) if executed else ()
                correct=r.get("status")==c.status and (not c.sql or (rows==c.expected and not r["truncated"]))
                # Replay the displayed query, compare every returned cell and verify the displayed numeric answer.
                consistent=None
                if executed:
                    from analyst import summarize
                    verified=db.execute(r["sql"])
                    consistent=rows==values(verified) and r["answer"]==summarize(verified,lang)
                runs.append({"kind":c.kind,"lang":lang,"question":getattr(c,lang),"correct":correct and r.get("lang")==lang,
                    "sql_returned":executed,"grounded_display":consistent,"latency_s":round(time.perf_counter()-before,3),
                    "result":r})
                print(c.kind,lang,r["status"],runs[-1]["correct"],flush=True)
        answered=[r for r in runs if r["sql_returned"]]
        expected_sql={c.kind for c in suite if c.sql}
        needed=[r for r in runs if r["kind"] in expected_sql]
        latency=sorted(r["latency_s"] for r in runs)
        import math
        report.update(mode="live",provider=p.name,model=p.model,runs=runs,metrics={
            "exact_correct":[sum(r["correct"] for r in runs),len(runs)],
            "returned_executed_sql_on_answerable":[sum(r["sql_returned"] for r in needed),len(needed)],
            "factual_display_consistency":[sum(r["grounded_display"] for r in answered),len(answered)],
            "latency_median_s":statistics.median(latency),"latency_p95_s":latency[math.ceil(.95*len(latency))-1]})
    if args.report:
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("cases","runs")},ensure_ascii=False))
    return int(args.live and any(not r["correct"] or r["grounded_display"] is False for r in report["runs"]))


if __name__=="__main__":
    try:
        sys.exit(run())
    except ProviderError as exc:
        raise SystemExit(str(exc))
