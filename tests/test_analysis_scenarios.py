"""Regression coverage for a previously failing Hackathon what-if prompt."""
import unittest
from unittest.mock import patch
from analyst import Analyst, _scenario_from_question, _validated_status_counts, apply_requested_format, status_analysis

PROMPT=("2024-yilda O‘zbekiston birjasida qayd etilgan bitimlarning bajarilish samaradorligini tahlil qil. "
"To‘liq bajarilgan bitimlarning jami bitimlardagi foiz ulushini hisobla. "
"Bekor qilingan va qisman bajarilgan bitimlarning umumiy soni va foizini aniqlagin. "
"Shuningdek, agar bekor qilingan bitimlar soni 20% ga kamayganida, to‘liq bajarilgan bitimlar soni o‘zgarmagan deb faraz qilib, "
"ularning jami bitimlardagi ulushi qanday bo‘lishini hisobla. "
"Bunda bekor qilingan bitimlar umumiy hisobdan chiqariladi deb ol. "
"Javobni oddiy o‘zbek tilida, faqat matn shaklida ber. Jadval tuzma. Barcha hisoblash formulalarini ko‘rsat va yakuniy xulosa chiqar.")

class AnalysisScenarioTests(unittest.TestCase):
    def setUp(self):
        self.result = {'status':'ok','lang':'uz','rows':[{'full_count':94481,'cancelled_count':7323,'partial_count':4843,'total_count':106647}], 'truncated':False}

    def test_exact_jury_prompt(self):
        result=apply_requested_format(dict(self.result),PROMPT)
        self.assertEqual(result['display_format'],'text')
        for s in ('94 481','7 323','4 843','106 647','88,59%', '6,87%', '4,54%', '11,41%',
                  '7,77 baravar','20%','1 464.60','89,83%','1,23 foiz punkt','Xulosa:', '÷','×'):
            self.assertIn(s,result['answer'])
        self.assertNotIn('|',result['answer'])

    def test_legacy_aliases(self):
        r=dict(self.result,rows=[{'full_exec':94481,'cancelled':7323,'partial_exec':4843,'total_deals':106647}])
        self.assertIn('89,83%',apply_requested_format(r,PROMPT)['answer'])

    def test_swapped_order_of_columns(self):
        r=dict(self.result,rows=[{'total_count':106647,'partial_count':4843,'full_count':94481,'cancelled_count':7323}])
        self.assertIn('89,83%',apply_requested_format(r,PROMPT)['answer'])

    def test_inconsistent_counts_no_calculation(self):
        r=dict(self.result,rows=[{'full_count':94481,'cancelled_count':7323,'partial_count':4843,'total_count':106646}])
        a=apply_requested_format(r,PROMPT)['answer']
        self.assertIn('yetarli',a)
        self.assertNotIn('89,83%',a)

    def test_missing_column_no_calculation(self):
        r=dict(self.result,rows=[{'full_count':94481,'cancelled_count':7323,'total_count':106647}])
        a=apply_requested_format(r,PROMPT)['answer']
        self.assertIn('yetarli',a)
        self.assertNotIn('89,83%',a)

    def test_truncated_no_calculation(self):
        r=dict(self.result,truncated=True)
        self.assertNotIn('89,83%',apply_requested_format(r,PROMPT)['answer'])

    def test_russian_scenario(self):
        q=('Проанализируй исполнение и аннулирование сделок в 2024 году. '
           'Если аннулированных сделок станет на 20% меньше, уменьшение исключить из общего числа сделок, '
           'а полностью исполненные сделки остаются без изменения, какая будет доля? Только текстом, без таблицы.')
        result=apply_requested_format(dict(self.result,lang='ru'),q)
        self.assertIn('89.83%',result['answer'])
        self.assertIn('Вывод:',result['answer'])
        self.assertEqual(result['display_format'],'text')

    def test_unspecified_scenario_abstains_from_what_if(self):
        q='Agar bekor qilingan bitimlar 30% kamaysa ulush nima bo‘ladi? Jadval tuzma'
        a=apply_requested_format(self.result,q)['answer']
        self.assertIn('aniq ko‘rsatish',a)
        self.assertNotIn('Yangi ulush formulasi',a)

    def test_unrelated_question_never_invents_stats(self):
        self.assertIsNone(status_analysis(self.result,'uz','Eng faol broker kim?'))

    def test_public_entrypoint_always_applies_format(self):
        agent=Analyst.__new__(Analyst)
        with patch.object(agent,'_ask_once',return_value=self.result):
            r=agent.ask(PROMPT, 'uz', [{'question':'Qaysi broker faol?','state':{'years':['2025']}}])
        self.assertEqual(r['display_format'],'text')
        self.assertIn('89,83%',r['answer'])

if __name__=='__main__': unittest.main()
