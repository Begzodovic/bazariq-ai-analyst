import unittest
from analyst import Analyst
from app import ROOT
from database import Register, QueryError
from semantic import structured_context, validate, extract_selected

class Semantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=Register(ROOT/'uzex.db')

    def test_selected_set_is_immutable_on_followup(self):
        prior=[{'question':'2025-yilda TOP-5 mahsulot', 'selected_set':['1001','1002'], 'prior_sql':'SELECT hs_code FROM contracts'}]
        state=structured_context(prior,'Ularning Toshkentdagi o‘rtacha qiymati?')
        self.assertEqual(state['selected_set'],['1001','1002'])
        with self.assertRaisesRegex(QueryError,'selected_set'):
            validate('Ularning Toshkentdagi o‘rtacha qiymati?',"SELECT count(*) FROM deals WHERE day >= '2025-01-01' AND region LIKE '%Toshkent%'",{'rows':[]},state,prior)
        validate('Ularning Toshkentdagi o‘rtacha qiymati?',"SELECT count(*) FROM deals WHERE day >= '2025-01-01' AND region LIKE '%Toshkent%' AND product IN ('1001','1002')",{'rows':[]},state,prior)

    def test_region_context_held(self):
        prior=[{'question':'Toshkentdagi TOP-5 mahsulot'}]
        state=structured_context(prior,'Shularning 2024-yildagi summasi')
        with self.assertRaisesRegex(QueryError,'region filter'):
            validate('Shularning 2024-yildagi summasi',"SELECT SUM(amount) FROM deals WHERE day >= '2024-01-01'",{'rows':[]},state,prior)

    def test_broker_both_roles_required(self):
        state=structured_context([],'Brokerlar TOP-10 ishtiroklar bo‘yicha')
        with self.assertRaisesRegex(QueryError,'seller AND buyer'):
            validate('Brokerlar TOP-10 ishtiroklar bo‘yicha',"SELECT seller_broker,COUNT(*) FROM deals GROUP BY seller_broker",{'rows':[]},state,[])
        with self.assertRaisesRegex(QueryError,'ADDED'):
            validate('Brokerlar TOP-10 ishtiroklar bo‘yicha',"SELECT seller_broker,buyer_broker,COUNT(DISTINCT id) FROM deals GROUP BY seller_broker,buyer_broker",{'rows':[]},state,[])

    def test_broker_invariant_blocks_wrong_totals(self):
        state=structured_context([],'Brokerlar TOP-10 ishtiroklar bo‘yicha')
        sql='SELECT seller_broker,buyer_broker,SUM(CASE WHEN seller_broker IS NOT NULL THEN 1 END) AS seller_count,SUM(CASE WHEN buyer_broker IS NOT NULL THEN 1 END) AS buyer_count FROM deals'
        with self.assertRaisesRegex(QueryError,'ARITHMETIC'):
            validate('Brokerlar TOP-10 ishtiroklar bo‘yicha',sql,{'rows':[{'seller_count':4128,'buyer_count':2656,'total':6692}]},state,[])
        validate('Brokerlar TOP-10 ishtiroklar bo‘yicha',sql,{'rows':[{'seller_count':4128,'buyer_count':2656,'total':6784}]},state,[])

    def test_actual_broker_appearances_vs_distinct_deals(self):
        sql="""WITH roles AS (
            SELECT seller_broker AS code, 'seller' role FROM deals WHERE seller_broker IS NOT NULL
            UNION ALL
            SELECT buyer_broker AS code, 'buyer' role FROM deals WHERE buyer_broker IS NOT NULL
        ) SELECT code, SUM(role='seller') seller_count, SUM(role='buyer') buyer_count,
        COUNT(*) total FROM roles GROUP BY code ORDER BY total DESC,code LIMIT 10"""
        result=self.db.execute(sql,analytical=True)
        self.assertEqual(len(result['rows']),10)
        validate('Brokerlar TOP-10 ishtiroklar bo‘yicha',sql,result,structured_context([],''),[])
        for row in result['rows']:self.assertEqual(row['seller_count']+row['buyer_count'],row['total'])

    def test_top_identifiers_capture(self):
        r={'columns':['hs_code','summa'], 'rows':[{'hs_code':'1234','summa':20},{'hs_code':'5678','summa':30}]}
        self.assertEqual(extract_selected(r,'TOP-2 mahsulot'),['1234','5678'])

    def test_previous_rate_requires_date(self):
        with self.assertRaisesRegex(QueryError,'DATE'):
            validate('Oldingi USD kursi?', 'SELECT rate FROM usd_rates ORDER BY day DESC LIMIT 2',{'rows':[{'rate':12000}],'columns':['rate']},structured_context([],''),[])

if __name__=='__main__':unittest.main()
