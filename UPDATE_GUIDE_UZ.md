# BazarIQ — kontekstni eslatish va jadvaldan keyingi xulosa

GitHub `Webcoder09/bazariq1` asosiy papkasida ushbu uchta faylni almashtiring:

- `analyst.py` — 2 yil ko‘rsatkichlari mavjud jadvaldan o‘sish/kamayish xulosasini hisoblaydi; noto‘g‘ri farqda tekshirilmagan xulosa yozmaydi.
- `app.py` — 422 va 503 xatolarini foydalanuvchiga texnik kodsiz tushuntiradi.
- `index.html` — xato yuz berganda yangi chat tugmasi ko‘rsatadi. Davomiy savolda oldingi muvaffaqiyatli jadvaldan tanlangan nomlar, kodlar va yilni yangi savolga ko‘chiradi, avtomatik yubormaydi.

So‘ng Commit changes va Render → Manual Deploy → Deploy latest commit.

Eslatma: bu matn va interfeys tuzatishi SQL/Gemini serverdagi xatoni bartaraf etganini anglatmaydi. `503` Gemini yoki tarmoq sababli yana chiqishi mumkin. Yangi chat esa xizmat tiklanishini kafolatlamaydi.

Tekshiruv: `python -m unittest discover -s tests -q` (101 lokal test), `node --check` orqali JavaScript sintaksisi. Jonli Render hali tekshirilmagan.

Bazaga (`uzex.db` yoki uning bo‘laklariga), `fastpath.py` va `provider.py`ga tegmang. GitHub'ga `.env` yuklamang.
