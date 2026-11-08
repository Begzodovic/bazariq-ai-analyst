# BazarIQ — ommaviy Render deploy

1. ZIP ichidagi **barcha fayllarni** GitHub repo ildiziga yuklang. `uzex.db.gz.part01` dan `uzex.db.gz.part04` gacha **to‘rtta qismni** yuklang; 233 MB `uzex.db` va katta `uzex.db.gz` fayllarini **yuklamang**. Zipning o‘zini yuklamang.
2. GitHub repo **private** bo‘lsin. `.env` va API kalitni GitHub’ga yuklamang.
3. Render → New → Blueprint → repository → `render.yaml` bo‘yicha deploy. `plan: starter` haq to‘lanadigan doimiy servisdir; kerak bo‘lsa `free` ga almashtirish mumkin, ammo uxlab qoladi.
4. Render Environment'da **faqat** `GEMINI_API_KEY`ni yangi, maxfiy kalit sifatida kiriting. Model va boshqa parametrlar `render.yaml`da.
5. `BAZARIQ_BASIC_USER`, `BAZARIQ_BASIC_PASSWORD` endi kerak emas. Sayt hammaga login va parolsiz ochiladi.
6. Birinchi startda to‘rtta `.part` fayli yig‘ilib, bazasi `/tmp` papkaga ochiladi. 233 MB disk joy talab qilinadi. `GET /health` orqali serverni tekshiring.
7. Saytni Incognito va boshqa telefonda tekshiring, o‘zbekcha/ruscha savollarni bering; faqat 200 emas, javobning arifmetik to‘g‘riligini ham tekshiring.
8. Oldin chatda ulashilgan Gemini API kalitini zudlik bilan bekor qilib yangisini yarating. Ochiq prototip API kvotasini sarflaydi; 30 so‘rov/daqiqalik server limiti qo‘yilgan, qo‘shimcha Google API kvota monitoringi zarur.
9. `BAZARIQ_AUDIT_COMPLEX=0` tezlik uchun tanlandi: lokal SQL validatsiyasi bor, ammo murakkab javoblar uchun ikkinchi AI-audit yo‘q. Barcha javoblarning 90 soniyada to‘g‘riligiga kafolat emas.
10. Render havolasini hakamlar formasiga kiriting va **Submit** bosing.
