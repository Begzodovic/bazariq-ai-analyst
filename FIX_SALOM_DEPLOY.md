# BazarIQ — salomlashish xatosi tuzatildi

## Nima tuzatildi?
- `salom`, `Salom!`, `Assalomu alaykum`, `Привет`, `Здравствуйте` hamda rahmat/spasibo kabi qisqa xabarlar AI yoki SQL ga yuborilmaydi.
- Natija 200 HTTP va oddiy, mos tildagi javob bilan qaytariladi.
- Oddiy salomlashuvdan keyin real ma'lumot so'rovi odatdagi SQL tekshiruviga o'tadi.
- Qolgan 422/503 sabablari alohida tekshiruvni talab qiladi; bu tuzatish barcha Gemini xatolarini davolamaydi.

## GitHub va Render'ga joylash
1. ZIP ichidagi `analyst.py` va `tests/test_greetings.py` ni GitHub repository asosiy papkasi va `tests` ichiga yuklang (Create/Upload files orqali). Agar faqat salomlashish tuzatishi kerak bo'lsa, boshqa fayllarni qayta yuklash shart emas.
2. GitHub commit saqlang.
3. Render -> Manual Deploy -> Deploy latest commit (Auto Deploy yoqilgan bo'lsa avtomatik).
4. `https://bazariq1.onrender.com` ni oching va `salom`, `Привет` ni tekshiring.
5. Murakkab savolda yana HTTP 422/503 chiqsa, o'sha savol va Render logs tafsilotini tekshiring.

## Xavfsizlik
- `.env` yoki API kalitni GitHubga yubormang.
- `uzex.db.gz.part01..04` fayllarini ayni tuzilishda qoldiring.

## Test
`python -m unittest discover -s tests -q` — 49 ta test OK (lokal). Jonli Gemini API testi emas.
