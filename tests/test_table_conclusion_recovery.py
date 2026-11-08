import unittest
from pathlib import Path
from analyst import apply_requested_format

ROWS=[
 {'Hudud':'Toshkent shahri','2024-yil (bekor)':1475,'2025-yil (bekor)':1688,'Farq (ta)':213,'O‘zgarish (%)':14.44},
 {'Hudud':'Namangan viloyati','2024-yil (bekor)':976,'2025-yil (bekor)':1071,'Farq (ta)':95,'O‘zgarish (%)':9.73},
 {'Hudud':'Buxoro viloyati','2024-yil (bekor)':520,'2025-yil (bekor)':728,'Farq (ta)':208,'O‘zgarish (%)':40},
 {'Hudud':'Samarqand viloyati','2024-yil (bekor)':527,'2025-yil (bekor)':614,'Farq (ta)':87,'O‘zgarish (%)':16.51},
 {'Hudud':'Toshkent viloyati','2024-yil (bekor)':625,'2025-yil (bekor)':543,'Farq (ta)':-82,'O‘zgarish (%)':-13.12},
]

class TestTableConclusion(unittest.TestCase):
 def make(self,rows=ROWS):return {'status':'ok','rows':rows,'lang':'uz','truncated':False,'answer':'Natijalarni jadvalga joyladim.'}
 def test_added_after_table(self):
  q='Jadvalda ko‘rsat va undan keyin qaysi hududda eng katta o‘sish va kamayish bo‘lganini xulosa qil.'
  result=apply_requested_format(self.make(),q)
  self.assertIn('Xulosa:',result['answer'])
  self.assertIn('Toshkent shahri',result['answer'])
  self.assertIn('Buxoro viloyati',result['answer'])
  self.assertIn('Toshkent viloyati',result['answer'])
  self.assertIn('213',result['answer'])
 def test_no_unsafe_conclusion_for_wrong_delta(self):
  rows=[dict(r) for r in ROWS];rows[0]['Farq (ta)']=999
  result=apply_requested_format(self.make(rows),'Jadvaldan keyin xulosa qil.')
  self.assertNotIn('Xulosa:',result['answer'])
 def test_no_conclusion_if_truncated(self):
  r=self.make();r['truncated']=True
  self.assertNotIn('Xulosa:',apply_requested_format(r,'Jadvaldan keyin xulosa qil.')['answer'])
 def test_browser_copy_context_and_retries(self):
  html=(Path(__file__).resolve().parents[1]/'index.html').read_text()
  self.assertIn('function prepareFreshQuestion(',html)
  self.assertIn('const q=prepareFreshQuestion(originalQuestion||"",sourceChat)',html)
  self.assertIn('[422,503,504].includes(resp.status)',html)
  self.assertIn('Yangi chatda sinab',html)

if __name__=='__main__':unittest.main()
