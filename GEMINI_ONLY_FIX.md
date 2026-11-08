# BazarIQ — Gemini-only broker follow-up fix (2026-11-05)

## Asosiy o‘zgarishlar
- AI provayder faqat Google Gemini. GROQ va XAI sozlamalari olib tashlandi.
- `GEMINI_API_KEY`, `GEMINI_MODEL` va `AI_TIMEOUT` sozlamalari ishlatiladi.
- 2025-yil Toshkent shahridagi bitimlarda oldingi TOP-5 brokerning sotuvchi/xaridor ishtiroklari mustaqil SQL bilan hisoblanadi (avvalgi ro‘yxat qayta tanlanmaydi).
- Brokerlar bo‘yicha TOP javobda `broker_code` mavjud bo‘lsa, u suhbat holatiga saqlanadi. Eski chatda kod bo‘lmasa, avvalgi SQL va to‘liq broker nomi orqali kod tiklanadi. Kodni ishonchli tiklash mumkin bo‘lmasa, agent boshqa TOP-5 uydirmasligi kerak.
- Toshkent shahri (deals.region = 'Toshkent shahri') Toshkent viloyatidan alohida. Sotuvchi + xaridor = jami, bir broker ikkala rolda chiqsa ikkita ishtirok.
- Brauzer tarmoq xatosi yoki HTTP xato kodini ko‘rsatadi, backend istisnolarini PowerShell terminaliga chiqaradi.

## Windows'da ishga tushirish
1. Oldingi server ishlayotgan PowerShell oynasida Ctrl+C bosing.
2. Ushbu ZIP'ni yangi papkaga chiqaring. Eski `.env` faylingizni yangi papkaga ko‘chiring (maxfiy API kalitni chatga yubormang).
3. `.env`da `GEMINI_API_KEY=...`, `GEMINI_MODEL=gemini-3.5-flash-lite` (yoki amalda ishlaydigan modelingiz), `AI_TIMEOUT=35` bo‘lsin. Boshqa provider kalitlari shart emas.
4. PowerShell: `py app.py --check-provider`, so‘ng `py app.py`.
5. Brauzerda http://localhost:8000; Ctrl+F5 bilan yangilang. Oldingi TOP-5'ni bir chatning o‘zida tanlang, keyin broker follow-up savolini bering.
6. Avtomatik test: `py -m unittest discover -s tests -v`.

## Agar `Serverga ulanib bo‘lmadi` chiqsa
- PowerShell server oynasida `BazarIQ: http://localhost:8000` yozuvi qolganini tekshiring.
- `http://localhost:8000/health` ochilishini tekshiring. HTTP 503 modelga ulanish muammosi, HTTP 500 esa server logida traceback chiqaradi.
- `netstat -ano | findstr :8000` bilan port bandligi aniqlanadi.
- Gemini tekshiruvi muvaffaqiyatli chiqqan bo‘lsa ham, keyingi ko‘p bosqichli so‘rovga model javob bermasligi mumkin. Ichki deadline 85 soniya; 90 soniyada barcha savollarga to‘g‘ri javob berish kafolatlanmaydi.

## Ma'lumot va sinov chegarasi
42 ta lokal avtomatik testdan o‘tdi. Haqiqiy Gemini API bilan hakamlar savollari bo‘yicha umumiy aniqlik va barcha savollarda 90 sekund cheklovi jonli tekshirilmagan. Lokal SQLite natijalari reyestrdagi ma'lumotlarni aks ettiradi, mustaqil audit emas.
