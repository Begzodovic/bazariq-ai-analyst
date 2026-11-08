# BazarIQ — sodda, foydalanuvchiga tushunarli javoblar

Yangilangan fayllar: `app.py`, `analyst.py`, `index.html`. Ularni GitHub repositoryning asosiy papkasida almashtiring; `.env` yoki Gemini API kalitini GitHub'ga yuklamang. Render avtomatik deploy qilmasa, `Manual Deploy -> Deploy latest commit`.

- Bo‘sh qatorlar: **Mazkur so‘rov bo‘yicha reyestrda natija topilmadi.** / **По данному запросу в реестре результаты не найдены.**
- Natija `NULL`: hisoblash uchun yetarli qiymat yo‘q; **0** bo‘lsa bu haqiqatdan nol va alohida ko‘rsatiladi.
- Reyestrda kerakli ma’lumot yo‘q: ma’lumot yetarli emasligi alohida tushuntiriladi.
- SQLite, davr tekshiruvi yoki audit xato bo‘lsa: **Javobni reyestrdan tekshirib bo‘lmadi. Savolni aniqlashtiring yoki qayta urinib ko‘ring.** Bu holat `natija topilmadi` deb talqin qilinmaydi.
- Gemini `503` yoki rate limit `429`: tushunarli vaqtinchalik xabar, foydalanuvchiga HTTP raqami ko‘rsatilmaydi.
- Batafsil xato server logida qoladi. Yangi matnlar SQL hisoblash, muddat tekshiruvlari yoki Gemini API xatolarini o‘z-o‘zidan tuzatmaydi.
