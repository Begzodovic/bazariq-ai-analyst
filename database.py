"""Read-only transaction register and bounded analytical SQL."""
import json
import math
import re
import sqlite3
import time
import unicodedata
from contextlib import closing
from pathlib import Path
from db_bootstrap import ensure_database


class QueryError(ValueError):
    pass


def fold(value):
    """Unicode-aware matching for Uzbek apostrophe variants and Cyrillic names."""
    if value is None:
        return None
    s = unicodedata.normalize("NFKC", str(value)).casefold()
    return re.sub(r"['‘’ʻʼ`ʹ]", "'", s).replace("ё", "е")


DIMENSIONS = {
    "deals": ("region", "unit", "status", "auction", "contract_type", "contract_form"),
    "contracts": ("currency", "category", "product_group", "industry", "region"),
    "participants": ("region", "role", "activity", "vat"),
}
RELATIONS = [
    ("deals.contract_id", "contracts.id"),
    ("deals.seller_inn", "participants.inn"), ("deals.buyer_inn", "participants.inn"),
    ("contracts.seller_inn", "participants.inn"),
    ("deals.seller_broker", "brokers.code"), ("deals.buyer_broker", "brokers.code"),
    ("deals.day", "usd_rates.day"),
]
FUNCTIONS = set("""
abs avg cast ceil ceiling char coalesce count cume_dist date datetime dense_rank first_value
floor fold ifnull iif instr julianday lag last_value lead length like likely lower ltrim
max min nth_value ntile nullif percent_rank printf rank replace round row_number rtrim sign
strftime substr substring sum time total trim typeof unixepoch unlikely upper
""".split())
TABLES = {"deals", "contracts", "participants", "brokers", "usd_rates"}


class Register:
    def __init__(self, path):
        self.path = ensure_database(path).resolve()
        self.schema = {}
        self.context = self.inspect()

    def connect(self):
        db = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=1)
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML, False)
        db.create_function("fold", 1, fold, deterministic=True)
        return db

    def inspect(self):
        labels = json.loads(Path(__file__).with_name("columns.json").read_text(encoding="utf8"))
        with closing(self.connect()) as db:
            available = {r[0] for r in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
            if not TABLES <= available:
                raise QueryError("Yetishmayotgan jadvallar / Нет таблиц: " + ", ".join(sorted(TABLES - available)))
            for table in sorted(TABLES):
                self.schema[table] = {
                    name: [typ, labels.get(table, {}).get(name, name), bool(pk)]
                    for _, name, typ, _, _, pk in db.execute(f"PRAGMA table_info({table})")
                }
            enums = {}
            for table, columns in DIMENSIONS.items():
                for column in columns:
                    if column in self.schema[table]:
                        sql = f"SELECT DISTINCT {column} FROM {table} ORDER BY 1 LIMIT 81"
                        enums[f"{table}.{column}"] = [r[0] for r in db.execute(sql)]
            # Group real contract names by code. Each code can cover several grades/
            # spellings, so short names are examples, not an exhaustive product list.
            products = {}
            for code, product in db.execute("""
                    SELECT DISTINCT hs_code, product FROM contracts
                    WHERE hs_code IS NOT NULL AND product IS NOT NULL
                    ORDER BY hs_code, length(product), product
                    """):
                names = products.setdefault(str(code), [])
                if len(names)<3 and product.casefold() not in {n.casefold() for n in names}:
                    names.append(product)
            coverage = db.execute("SELECT MIN(day),MAX(day) FROM deals").fetchone()
            samples = {}
            for table in self.schema:
                cols = [k for k in self.schema[table] if k in ("day", "product", "code", "rate", "unit", "quantity", "lot")]
                if cols:
                    samples[table] = dict(zip(cols, db.execute(f"SELECT {','.join(cols)} FROM {table} LIMIT 1").fetchone() or ()))
        return {"columns_type_label_pk": self.schema, "many_to_one": RELATIONS, "values": enums,
                "product_codes_with_name_examples": products, "deal_date_coverage": coverage, "sample_values": samples}

    def execute(self, sql, *, row_limit=100, seconds=8, analytical=False):
        if not isinstance(sql, str) or not re.match(r"^\s*(SELECT|WITH)\b", sql, re.I) or len(sql) > 16000:
            raise QueryError("Expected one SELECT or WITH … SELECT (maximum 16000 characters).")
        sources, accesses = set(), set()
        def authorize(action, arg1, arg2, dbname, view):
            if action == sqlite3.SQLITE_READ and arg1 in self.schema and dbname in (None, "main"):
                if not arg2 or arg2 in self.schema[arg1]:
                    sources.add(arg1)
                    accesses.add(f"{arg1}.{arg2 or '*'}")
                    return sqlite3.SQLITE_OK
            if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and arg2 in FUNCTIONS:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        deadline = time.monotonic() + seconds
        with closing(self.connect()) as db:
            db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 65536)
            db.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 80)
            db.setlimit(sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 15)
            db.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 64)
            db.setlimit(sqlite3.SQLITE_LIMIT_LIKE_PATTERN_LENGTH, 500)
            db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            db.set_authorizer(authorize)
            try:
                # SQLite prepares the exact statement, resolving even unexecuted branches.
                db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
                if not sources:
                    raise QueryError("The query must read an authorized register table.")
                if analytical:
                    program = db.execute("EXPLAIN " + sql).fetchall()
                    # SELECT <literal> FROM deals can pass the table authorizer. Reject an
                    # unconditional literal projection immediately feeding a result row.
                    literal_ops = {"Integer","Int64","Real","String8","String","Blob"}
                    for index, (_, op, start, count, *_) in enumerate(program):
                        if op == "ResultRow":
                            assigned = set()
                            for inst in reversed(program[:index]):
                                if inst[1] not in literal_ops:
                                    break
                                assigned.add(inst[3])
                            if set(range(start, start+count)) <= assigned:
                                raise QueryError("Return values calculated from stored fields, not literal results.")
                cur = db.execute(sql)
                names = [desc[0] for desc in cur.description]
                if len(set(n.casefold() for n in names)) != len(names):
                    raise QueryError("Give each output column a unique alias.")
                rows = cur.fetchmany(row_limit + 1)
                if any(isinstance(v, bytes) for row in rows for v in row):
                    raise QueryError("Binary outputs are unsupported.")
                if any(isinstance(v, float) and not math.isfinite(v) for row in rows for v in row):
                    raise QueryError("Non-finite calculation. Check units and denominator.")
            except sqlite3.Error as exc:
                raise QueryError(str(exc)) from exc
        return {"sql":sql, "columns":names, "rows":[dict(zip(names, r)) for r in rows[:row_limit]],
                "truncated":len(rows) > row_limit, "source":sorted(sources), "reads":sorted(accesses)}
