"""Deterministic semantic constraints; never assume a successful SELECT is a correct answer."""
import re
from database import QueryError, fold

YEARS = re.compile(r'(?<!\d)(?:19|20)\d{2}(?!\d)')
REGION_WORDS = ('toshkent', 'ташкент', 'andijon', 'андижан', 'samarqand', 'самарканд', 'buxoro', 'бухар', 'farg', 'ферган', 'namangan', 'наманган', 'navoiy', 'навои', 'xorazm', 'хорезм', 'qashqad', 'кашкадар', 'surxond', 'сурхандар', 'jizzax', 'джизак', 'sirdaryo', 'сырдар', 'qoraqalpoq', 'каракалп')
FOLLOWUP_WORDS = ('ular', 'ularning', 'shular', 'shu', 'o‘sha', 'oʻsha', "o'sha", 'avvalgi', 'oldingi', 'ushbu', 'bu mahsulot', 'bu broker', 'endi', 'solishtir', 'taqqosla', 'foiz', 'o‘rtacha', 'ortacha', 'их', 'этих', 'эти', 'те же', 'предыдущ', 'теперь', 'сравни', 'процент', 'средн', 'shu hudud')


def _year_list(q):
    return YEARS.findall(q)


def is_followup(q, turns):
    q=fold(q)
    explicit=any(w in q for w in FOLLOWUP_WORDS)
    independent=any(w in q for w in ('brokerlar','брокеры','mahsulotlar','товары','shartnomalar','контракты','broker royxat','список брокеров'))
    return bool(turns) and (explicit or (len(q.split()) <= 6 and not independent and not _year_list(q)))


def structured_context(turns, question):
    """Reconstruct state from documented conversation, with current question taking priority.
    Store exact selected IDs, not just a phrase such as 'top five'.
    """
    state={'years':[], 'region':None, 'region_type':None, 'selected_set':[], 'metric':None,
           'broker':None, 'product':None, 'comparison':None, 'turns':[]}
    if not isinstance(turns,list): return state
    for t in turns[-12:]:
        if not isinstance(t,dict) or not isinstance(t.get('question'),str): continue
        q=fold(t['question'])
        yrs=_year_list(q)
        if yrs: state['years']=yrs
        for name in REGION_WORDS:
            if name in q: state['region']=name;state['region_type']='deal_region';break
        if ('sotuvchi hududi' in q or 'продавца регион' in q): state['region_type']='seller_region'
        elif ('xaridor hududi' in q or 'покупателя регион' in q): state['region_type']='buyer_region'
        if any(x in q for x in ('bitim', 'сделк')): state['metric']='deal_count'
        if any(x in q for x in ('ishtirok', 'участи')): state['metric']='role_appearances'
        if 'foiz' in q or 'процент' in q: state['comparison']='pct_change'
        if 'taqqos' in q or 'сравн' in q: state['comparison']='compare'
        # Actual IDs chosen in previous results are immutable unless user requests a new ranking.
        if isinstance(t.get('selected_set'),list):
            items=[str(x) for x in t['selected_set'] if x is not None][:100]
            if items: state['selected_set']=items
        if isinstance(t.get('state'),dict):
            old=t['state']
            if isinstance(old.get('selected_set'),list) and old['selected_set']:
                state['selected_set']=[str(x) for x in old['selected_set']][:100]
        state['turns'].append({'question':t['question'][:300], 'prior_sql':str(t.get('prior_sql',''))[:1200]})
    current=fold(question)
    yrs=_year_list(current)
    if yrs: state['years']=yrs
    for name in REGION_WORDS:
        if name in current: state['region']=name; state['region_type']='deal_region'; break
    if 'sotuvchi hududi' in current or 'регион продавца' in current: state['region_type']='seller_region'
    elif 'xaridor hududi' in current or 'регион покупателя' in current: state['region_type']='buyer_region'
    return state


def extract_selected(result, question):
    """Only retain real code identifiers from result rows; never infer codes from names."""
    if not re.search(r'\b(?:top|топ)\s*[-–]?\s*\d+|eng ko.p|самых|birinchi\s+\d+',fold(question)):
        return []
    for key in result.get('columns',[]):
        k=fold(key)
        if k in ('hs_code','product_code','mahsulot_kodi','tovar_kodi','код_товара','код товара','код тн вэд','kod','код', 'broker_code', 'broker_kodi', 'broker kodi', 'код брокера', 'брокер код', 'code'):
            values=[str(r[key]) for r in result.get('rows',[]) if r.get(key) is not None]
            if values and len(values)<=100:return list(dict.fromkeys(values))
    # A TOP-N query may return the broker name but omit its code. The caller
    # resolves names to actual broker codes instead of memorizing display strings.
    return []


def _quoted(sql, value):
    return bool(re.search(r"['\"]"+re.escape(str(value))+r"['\"]",sql,re.I))


def validate(question, sql, result, state, prior, *, db=None):
    q=fold(question)
    s=fold(sql)
    # Check carry-forward conditions only for an actual follow-up.
    follow=is_followup(question,prior)
    if follow:
        region=state.get('region')
        if region and not any(x in s for x in (region,region.replace('toshkent','ташкент'),region.replace('ташкент','toshkent'))):
            raise QueryError('SEMANTIC: earlier region filter was lost; preserve the region dimension and its type.')
        if state.get('region_type')=='seller_region' and 'seller_inn' not in s:
            raise QueryError('SEMANTIC: seller registered region requires a participants join on d.seller_inn, NOT d.region.')
        if state.get('region_type')=='buyer_region' and 'buyer_inn' not in s:
            raise QueryError('SEMANTIC: buyer registered region requires a participants join on d.buyer_inn, NOT d.region.')
        # Previous selected TOP-N must be held fixed. A re-ranking is forbidden.
        items=state.get('selected_set') or []
        new_rank=bool(re.search(r'\b(?:yangi|new|другие|новый)\b',q))
        if items and not new_rank:
            absent=[v for v in items if not _quoted(sql,v)]
            if absent:
                raise QueryError('SEMANTIC: reuse the exact prior selected_set codes: '+', '.join(items[:20])+'. Use a VALUES/CTE and LEFT JOIN to preserve zero rows; do NOT recalculate TOP-N.')
        # An old year is a constraint only if a newer year wasn't expressly supplied.
        if not _year_list(question) and state.get('years'):
            years=state['years']
            if any(y not in s and str(int(y)+1) not in s for y in years):
                raise QueryError('SEMANTIC: inherited year was dropped: '+', '.join(years))
    broker_context = 'broker' in q or 'брокер' in q or (follow and state.get('metric')=='role_appearances')
    appearances=broker_context and any(w in q for w in ('ishtirok','участи','qatnash','рол','ikki tomon','обе стороны','jami','всего'))
    if appearances and any(w in q for w in ('jami','всего','ikki tomon','обе стороны','top','топ','ishtirok','участи')):
        if 'seller_broker' not in s or 'buyer_broker' not in s:
            raise QueryError('SEMANTIC: broker appearances must include seller AND buyer roles, UNION ALL or two SUM(CASE...) expressions. COUNT(DISTINCT d.id) is not appearances.')
        if not (('union all' in s) or ('case' in s and 'sum(' in s) or ('seller_count' in s and 'buyer_count' in s)):
            raise QueryError('SEMANTIC: both broker-role counts need to be ADDED, not deduplicated by deal id.')
    # If caller asked for an explicitly role-specific broker count, the role predicate is mandatory.
    if broker_context and any(w in q for w in ('faqat sotuvchi','sotuvchi sifatida','только продав','как продавец')) and 'seller_broker' not in s:
        raise QueryError('SEMANTIC: seller appearances require d.seller_broker = broker code.')
    if broker_context and any(w in q for w in ('faqat xaridor','xaridor sifatida','только покуп','как покупатель')) and 'buyer_broker' not in s:
        raise QueryError('SEMANTIC: buyer appearances require d.buyer_broker = broker code.')
    # Arithmetical invariant on any returned triplet with a clear seller/buyer/total meaning.
    for row in result.get('rows',[]):
        keys=list(row)
        def col(words):
            return next((k for k in keys if any(w in fold(k) for w in words) and isinstance(row[k],(int,float))),None)
        seller=col(('seller','sotuvchi','продав'))
        buyer=col(('buyer','xaridor','покуп'))
        total=col(('total','jami','всего','итого'))
        if seller and buyer and total and len({seller,buyer,total})==3:
            a,b,c=row[seller],row[buyer],row[total]
            if abs((a+b)-c)>max(1e-6,abs(c)*1e-9):
                raise QueryError(f'ARITHMETIC: {seller} + {buyer} must equal {total}, but {a} + {b} != {c}.')
    # Explicit conditional rate checks.
    if ('курс' in q or 'kurs' in q) and ('oldingi' in q or 'предыдущ' in q):
        if not any('day' in fold(k) or 'sana' in fold(k) or 'дата' in fold(k) for k in result.get('columns',[])):
            raise QueryError('SEMANTIC: report the previous existing rate DATE, not only the rate.')
    return True
