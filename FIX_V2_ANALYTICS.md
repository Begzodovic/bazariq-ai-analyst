# BazarIQ: hisoblash va javob formatlash tuzatishi

## Nima tuzatildi
- SQL qaytargan `full_count`, `partial_count`, `cancelled_count`, `total_count` kabi ustunlar va oldingi `full_exec`, `partial_exec`, `cancelled`, `total_deals` nomlari bitta tasdiqlangan metrikalarga bog‘lanadi.
- To‘liq, qisman, bekor qilingan bitimlar va jami miqdorlar bir-biriga tengligi tekshiriladi. Yetishmagan yoki nomuvofiq sonlarda foiz va ssenariy taxmin qilinmaydi.
- Aynan ifodalangan ssenariy (bekor qilinganlar X% kamayadi, kamayganlar jamidan chiqariladi, to‘liq bajarilganlar o‘zgarmaydi) alohida arifmetika va formula bilan hisoblanadi. Boshqa noaniq faraziy shartlarda taxmin qilmaydi.
- `jadval tuzma`, `faqat matn`, `без таблицы` kabi talablar kuchda qoladi. `index.html` yangilanishi shart emas, agar avvalgi text-only versiya o‘rnatilgan bo‘lsa.
- Python raqamni ikki kasrgacha chiqaradi. Ssenariydagi 1464.60 — nazariy hisob. Asl reyestrdagi bitimlar soni butun sonligicha qoladi.

## GitHub + Render
1. `analyst.py` ni repository asosiy papkasidagi shu nomli faylga almashtiring.
2. `Commit changes` qiling. Render avtomatik deploy qilmasa `Manual Deploy -> Deploy latest commit`.
3. Render'da `Live` bo‘lgach, savolni *yangi chatda* va *eski chatda* sinang.
4. Yangi savolda `full_count`, `cancelled_count`, `partial_count`, `total_count` qaytganda 88,59%, 11,41%, 89,83% va 1,23 foiz punkt chiqishi kerak.

## Testlar
`python -m unittest discover -s tests -q`
84/84 lokal testdan o'tdi (2026-11-05). API bilan jonli Render testi hali o‘tkazilmagan. Barcha mumkin bo‘lgan savollarga to‘g‘ri javob kafolatlanmaydi.

## Xavfsizlik
`.env` yoki Gemini API kalitini GitHub'ga yuklamang. Kalitni Render Environment'da saqlang. Eski oshkor qilingan kalitni bekor qiling.
