"""Exact intent handlers for straightforward registry questions; no LLM/network needed.
Never use fuzzy matches for values, identifiers, filters or ambiguous requests.
"""
import re
import sqlite3
import time
from contextlib import closing
from database import fold, QueryError

TABLE_WORDS = {
 'brokers': ('broker', 'брокер'),
 'participants': ('ishtirokchi', 'иштирокник', 'участник', 'qatnashchi'),
 'contracts': ('shartnoma', 'контракт', 'договор'),
 'deals': ('bitim', 'битим', 'сделк', 'savdo'),
 'usd_rates': ('kurs', 'курс', 'валют', 'usd', 'dollar'),
}
LIST = ('royxat', "ro'yxat", 'roʻyxat', 'ro‘yxat', 'ro’yxat', 'перечень', 'список', 'sanab', 'ko‘rsat', 'koʻrsat', 'ko\'rsat', 'покажи', 'выведи', 'nomlari', 'названи', 'kimlar', 'qaysilar')
COUNT = ('nechta', 'qancha', 'soni', 'количеств', 'сколько', 'число', 'jami')
LATEST = ('oxirgi', 'eng so‘nggi', 'eng soʻnggi', "eng so'nggi", 'so‘nggi', 'soʻnggi', 'последн', 'самый свеж', 'актуальн', 'eng yangi')

def _fixed_read(db, sql, *, row_limit, seconds, source):
    """Run ONLY developer-authored fixed SQL from this module.

    This does not process model-generated SQL. The connection remains OS-level
    read-only and PRAGMA query_only. It avoids SQLite-version differences in
    the *arbitrary SQL* authorizer for these pre-vetted report queries.
    """
    if not re.match(r"^\s*(?:SELECT|WITH)\b", sql, re.I) or ";" in sql:
        raise QueryError("Invalid fixed reporting query")
    deadline=time.monotonic()+seconds
    with closing(db.connect()) as connection:
        connection.set_progress_handler(lambda: int(time.monotonic()>=deadline), 1000)
        try:
            cursor=connection.execute(sql)
            names=[item[0] for item in cursor.description]
            rows=cursor.fetchmany(row_limit+1)
        except sqlite3.Error as exc:
            raise QueryError(f"Fixed reporting query failed: {type(exc).__name__}") from exc
    return {"sql":sql,"columns":names,"rows":[dict(zip(names,r)) for r in rows[:row_limit]],
            "truncated":len(rows)>row_limit,"source":source,"reads":[]}


def region_top_five(db, question, lang):
    """Auditable deterministic regional trade ranking (no Gemini call).

    Only activate on explicit independent top-5 *deal-region* questions asking
    for deal count, total UZS value, and republic-wide percentage in a year.
    Never guess the meaning of a participant's registration region.
    """
    q = fold(question)
    years = re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", q)
    if len(years) != 1 or not ("регион" in q or "hudud" in q or "viloyat" in q):
        return None
    if not ("сдел" in q or "bitim" in q):
        return None
    if not re.search(r"(?:top\s*[-–]?\s*5|топ\s*[-–]?\s*5|5\s+(?:регион|hudud|viloyat)|пять\s+регион|beshta\s+hudud)", q):
        return None
    if not ("процент" in q or "дол" in q or "foiz" in q or "ulush" in q):
        return None
    if not ("сум" in q or "uzs" in q or "so'm" in q or "so‘m" in q or "soʻm" in q):
        return None
    # A country-wide regional trade ranking, not seller/buyer residence.
    if any(v in q for v in ("продавц", "покупат", "sotuvchi", "xaridor", "регистр", "ro'yxatdan")):
        return None
    year = int(years[0])
    since, until = f"{year}-01-01", f"{year+1}-01-01"
    lower, upper = db.context["deal_date_coverage"]
    if lower is None or upper is None or until <= lower or since > upper:
        return None
    # First ensure every trade can be converted; never silently omit sums.
    missing = _fixed_read(db, f"""
        SELECT COUNT(*) AS missing_count FROM deals d
        LEFT JOIN contracts c ON c.id = d.contract_id
        LEFT JOIN usd_rates r ON r.day = d.day
        WHERE d.day >= '{since}' AND d.day < '{until}'
        AND (c.currency IS NULL
           OR c.currency NOT IN ('Узбекский сум','Доллар США')
           OR (c.currency = 'Доллар США' AND r.rate IS NULL))
    """, row_limit=1, seconds=8, source=["deals","contracts","usd_rates"])
    missing_count = missing["rows"][0]["missing_count"]
    if missing_count:
        # We cannot truthfully give an all-deal UZS total.
        return {"status":"unavailable", "lang":lang,
                "answer":(f"Нельзя корректно посчитать сумму всех сделок: у {missing_count} сделок нет подтверждённой валюты или курса USD."
                          if lang=="ru" else f"Barcha bitimlar summasini aniq hisoblab bo‘lmaydi: {missing_count} ta bitim uchun valyuta yoki USD kursi mavjud emas."),
                "rows":[], "sql":missing["sql"]}
    if lang == "ru":
        cols = ('Регион','Количество сделок','Сумма торгов (сум)','Доля по республике (%)')
    else:
        cols = ('Hudud','Bitimlar soni','Savdo summasi (so‘m)','Respublika ulushi (%)')
    # Region is deals.region, and percentage denominator includes all national
    # trades in this same year, including rows with no assigned region.
    sql=f"""WITH period AS (
       SELECT d.region AS region, d.amount AS amount,
         c.currency AS currency, r.rate AS usd_rate
       FROM deals d
       LEFT JOIN contracts c ON c.id=d.contract_id
       LEFT JOIN usd_rates r ON r.day=d.day
       WHERE d.day >= '{since}' AND d.day < '{until}'
    ), totals AS (SELECT COUNT(*) AS n FROM period), ranked AS (
       SELECT region, COUNT(*) AS deals_count,
         SUM(CASE WHEN currency='Узбекский сум' THEN amount
                  WHEN currency='Доллар США' THEN amount*usd_rate END) AS sum_uzs
       FROM period GROUP BY region
    )
    SELECT region AS "{cols[0]}", deals_count AS "{cols[1]}",
      ROUND(sum_uzs,2) AS "{cols[2]}",
      ROUND(100.0 * deals_count / NULLIF((SELECT n FROM totals),0),2) AS "{cols[3]}"
    FROM ranked ORDER BY deals_count DESC, region LIMIT 5"""
    return _fixed_read(db, sql, row_limit=5, seconds=12, source=["deals","contracts","usd_rates"])



def compare_tashkent_namangan(db, question, lang):
    """Recompute explicit Tashkent city versus Namangan trade counts, without LLM.

    Deliberately narrow: an explicitly requested full-year comparison of these
    two deal geographies, not participants' registered addresses.
    """
    q = fold(question)
    years = re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", q)
    if len(years) != 1:
        return None
    if not (('ташкент' in q or 'toshkent' in q) and ('наманган' in q or 'namangan' in q)):
        return None
    if not ('сдел' in q or 'bitim' in q):
        return None
    if not ('сравн' in q or 'taqqos' in q or 'solishtir' in q):
        return None
    if any(x in q for x in ('областной ташкент', 'ташкентской области', 'toshkent viloyati',
                            'продавц', 'покупател', 'sotuvchi', 'xaridor', 'регистр')):
        return None
    if not ('город' in q or 'shahar' in q or 'shahr' in q or 'г.' in q):
        return None
    year = int(years[0]); low, high = db.context['deal_date_coverage']
    since, until = f"{year}-01-01", f"{year+1}-01-01"
    if low is None or high is None or until <= low or since > high:
        return {'status':'unavailable', 'lang':lang,
                'answer':('За указанный год в реестре нет данных.' if lang=='ru' else
                          'Ko‘rsatilgan yil bo‘yicha reyestrda ma’lumot mavjud emas.'),
                'rows':[], 'sql':''}
    sql = ("SELECT region, COUNT(*) AS deals_count FROM deals "
           f"WHERE day >= '{since}' AND day < '{until}' "
           "AND region IN ('Toshkent shahri','Namangan viloyati') "
           "GROUP BY region ORDER BY region")
    result = _fixed_read(db, sql, row_limit=2, seconds=8, source=["deals"])
    counts={r['region']:r['deals_count'] for r in result['rows']}
    if len(counts)!=2:
        return {'status':'unavailable','lang':lang,
                'answer':('В реестре не хватает данных для сравнения двух регионов.' if lang=='ru' else
                          'Ikkita hududni solishtirish uchun reyestrda yetarli ma’lumot yo‘q.'),
                'rows':result['rows'], 'sql':result['sql']}
    city=counts['Toshkent shahri']; region=counts['Namangan viloyati']
    delta=city-region
    if region == 0:
        pct = None
    else:
        pct = round(delta / region * 100, 2)
    percent = f'{pct:.2f}'.replace('.', ',') if pct is not None else 'не определён'
    if lang=='ru':
        answer=(f'За {year} год: в городе Ташкенте — {city:,} сделок, в Наманганской области — {region:,} сделок. '
                f'Разница: {delta:,} сделок. Формула: {city:,} − {region:,} = {delta:,}; '
                + (f'({city:,} − {region:,}) / {region:,} × 100% = {percent}%. '
                   if region else 'Процент вычислить нельзя: в Наманганской области 0 сделок. ')
                + 'Процент рассчитан относительно Наманганской области, по месту сделки.')
        columns=('Регион','Количество сделок')
        labels=('г. Ташкент','Наманганская область')
    else:
        answer=(f'{year}-yilda Toshkent shahrida {city:,} ta, Namangan viloyatida {region:,} ta bitim. '
                f'Farq: {delta:,} ta. Formula: {city:,} − {region:,} = {delta:,}; '
                + (f'({city:,} − {region:,}) / {region:,} × 100% = {pct:.2f}%. '
                   if region else 'Foizni hisoblab bo‘lmaydi: Namangan ko‘rsatkichi 0. ')
                + 'Foiz Namangan viloyatiga nisbatan hisoblangan.')
        columns=('Hudud','Bitimlar soni')
        labels=('Toshkent shahri','Namangan viloyati')
    result['columns']=list(columns)
    result['rows']=[{columns[0]:labels[0],columns[1]:city},
                    {columns[0]:labels[1],columns[1]:region}]
    result.update({'status':'ok','lang':lang,'answer':answer,'note':
                   'Сделки подсчитаны в SQLite по deals.region и deals.day.' if lang=='ru' else
                   'Bitimlar deals.region va deals.day orqali SQLite da hisoblandi.',
                   'ai_status':'not_needed','selected_set':[],
                   'state':{'years':[str(year)],'metric':'deal_count','region_type':'deal_region',
                            'regions':['Toshkent shahri','Namangan viloyati']}})
    return result




def broker_top_five(db, question, lang):
    """Direct, exact yearly TOP-5 broker ROLE APPEARANCES (no Gemini dependency).

    One deal can contribute one seller role and one buyer role. The combined
    role total is not a count of distinct deal IDs. Do not match requests with
    region, product, status, currency or other additional constraints.
    """
    q = fold(question)
    years = re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", q)
    if len(years) != 1 or not ("broker" in q or "брокер" in q):
        return None
    if not re.search(r"(?:top\s*[-–]?\s*5|топ\s*[-–]?\s*5|eng ko.p.*(?:5|beshta)|наибольш.*(?:5|пять))", q):
        return None
    if not ("sotuvchi" in q and "xaridor" in q or "продав" in q and "покуп" in q):
        return None
    if not ("bitim" in q or "сдел" in q or "ishtirok" in q or "участи" in q):
        return None
    if any(x in q for x in ("toshkent", "ташкент", "viloyat", "hudud", "регион", "област", "mahsulot", "tovar", "товар", "status", "статус", "bekor", "отмен", "usd", "summa", "сумм", "2024 va 2025", "2024 и 2025")):
        return None
    year = int(years[0])
    lo, hi = db.context["deal_date_coverage"]
    since, until = f"{year}-01-01", f"{year+1}-01-01"
    if lo is None or hi is None or until <= lo or since > hi:
        return None
    sql = f"""WITH appearances AS (
      SELECT seller_broker AS broker_code, COUNT(*) AS seller_n, 0 AS buyer_n
      FROM deals WHERE day >= '{since}' AND day < '{until}'
        AND seller_broker IS NOT NULL GROUP BY seller_broker
      UNION ALL
      SELECT buyer_broker AS broker_code, 0 AS seller_n, COUNT(*) AS buyer_n
      FROM deals WHERE day >= '{since}' AND day < '{until}'
        AND buyer_broker IS NOT NULL GROUP BY buyer_broker
    )
    SELECT b.code AS broker_code, b.name AS broker_name,
      SUM(a.seller_n) AS seller_count, SUM(a.buyer_n) AS buyer_count,
      SUM(a.seller_n) + SUM(a.buyer_n) AS total_count
    FROM appearances a JOIN brokers b ON b.code=a.broker_code
    GROUP BY b.code,b.name
    ORDER BY total_count DESC, b.code LIMIT 5"""
    raw = _fixed_read(db, sql, row_limit=5, seconds=12, source=["deals", "brokers"])
    records = raw['rows']
    if not records:
        return None
    chosen = [r['broker_code'] for r in records]
    if lang == 'ru':
        fields=('Брокер','В роли продавца','В роли покупателя','Всего участий')
        leading='За '+str(year)+' год наибольшее число участий в сделках у брокера'
        note='Считались участия брокеров в ролях продавца и покупателя; это не число уникальных сделок.'
    else:
        fields=('Broker','Sotuvchi sifatida','Xaridor sifatida','Jami ishtirok')
        leading=str(year)+'-yilda bitimlarda eng ko‘p qatnashgan broker'
        note='Sotuvchi va xaridor sifatidagi broker ishtiroklari alohida sanaldi; bu noyob bitimlar soni emas.'
    public_rows=[{fields[0]:r['broker_name'],fields[1]:r['seller_count'],
                  fields[2]:r['buyer_count'],fields[3]:r['total_count']} for r in records]
    best=records[0]
    diff=best['seller_count']-best['buyer_count']
    if lang=='ru':
        answer=(f"{leading} — {best['broker_name']}: {best['total_count']:,} участий "
                f"({best['seller_count']:,} в роли продавца и {best['buyer_count']:,} в роли покупателя). "
                f"Разница: {best['seller_count']:,} − {best['buyer_count']:,} = {diff:,}. "
                f"{note}")
    else:
        answer=(f"{leading} — {best['broker_name']}: {best['total_count']:,} ta ishtirok "
                f"(sotuvchi sifatida {best['seller_count']:,}, xaridor sifatida {best['buyer_count']:,}). "
                f"Farq: {best['seller_count']:,} − {best['buyer_count']:,} = {diff:,}. {note}")
    return {**raw,'rows':public_rows,'columns':list(fields),'status':'ok','lang':lang,
            'answer':answer,'note':note,'ai_status':'not_needed',
            'selected_set':chosen,
            'state':{'years':[str(year)],'metric':'role_appearances',
                     'selected_set':chosen}}

def run(db, question, lang):
    q=fold(question).strip()
    # Keep deliberately narrow: any extra constraints must go to the planner.
    words=q.split()
    table_hits=[t for t,terms in TABLE_WORDS.items() if any(term in q for term in terms)]
    if len(table_hits)!=1: return None
    t=table_hits[0]
    if re.search(r'\b(?:19|20)\d{2}\b|\d{2}[./-]\d{2}|\b(?:qaysi|какой)\s+(?:viloyat|област)',q): return None
    if any(s in q for s in ('bo‘yicha','boyicha','boʻyicha',' по ', 'hudud', 'регион', 'sotuvchi', 'xaridor', 'продав', 'покуп', '202', 'eng ko‘p', 'eng kop', 'топ', 'max', 'min', 'orasida', 'uchun', 'uchаст', 'yirik', 'крупн')): return None
    if t=='usd_rates' and any(x in q for x in LATEST) and any(x in q for x in ('kurs','курс','usd','dollar')):
        sql="SELECT day AS sana, rate AS usd_kursi_uzs FROM usd_rates ORDER BY day DESC LIMIT 1" if lang=='uz' else "SELECT day AS дата, rate AS курс_usd_uzs FROM usd_rates ORDER BY day DESC LIMIT 1"
    elif t in ('brokers','participants','contracts','deals') and any(x in q for x in COUNT) and len(words)<=9 and not any(x in q for x in LIST):
        label='soni' if lang=='uz' else 'количество'
        sql=f'SELECT count(*) AS {label} FROM {t}'
    elif t=='brokers' and any(x in q for x in LIST) and len(words)<=12:
        sql='SELECT code AS kod, name AS nomi, region AS hudud FROM brokers ORDER BY name, code' if lang=='uz' else 'SELECT code AS код, name AS название, region AS регион FROM brokers ORDER BY name, code'
    else:
        return None
    result=db.execute(sql,row_limit=500,analytical=True)
    return result
