# BazarIQ: RU / UZ jonli tarjima — V3

Bu paket avvalgi LANGUAGE SWITCH V2 tuzatishlarini HAM o'z ichiga oladi. Eski ZIPni alohida o'rnatmang.

## GitHub / Render

1. ZIP ichidagi `index.html`, `app.py`, `translation.py` fayllarini GitHub repositoryning ildiz katalogiga yuklang va mavjud fayllarni almashtiring.
2. **Yangi fayl** `translation.py` ham repositoryga qo'shilishi shart, aks holda server ishga tushmaydi.
3. `Commit changes` bosing.
4. Render'da oxirgi commitni deploy qiling; yangi yuklangan sahifani Ctrl+Shift+R bilan yangilang.
5. RU tugmasini bosing; chatdagi eski javob matni va jadvaldagi hudud/ustun nomlari tarjima bo'lishini tekshiring. UZ tanlanganda asl tilga qaytadi.

## Xavfsizlik va cheklovlar

- SQL qayta ishlamaydi; faqat ekranda ko'rsatiladigan matn tarjima qilinadi. Son va kodlar asl reyestr qiymatida qoladi.
- `RU` / `UZ` tugmasi bosilganda eski matnni to'liq tarjima qilish uchun server Gemini'ga **yangi tarjima so'rovi** yuboradi. Demak, internet, API kalit/quota va bir oz vaqt talab qilinadi. Tarjimalar chat tarixida saqlanadi.
- Ma'lum hudud nomlari va ustun sarlavhalari tezkor lug'at orqali ko'rsatiladi; boshqa matnlar Gemini orqali tarjima qilinadi.
- Gemini javob bermasa, noto'g'ri tarjima fakt sifatida ko'rsatilmaydi: tilga mos tarjima xatosi chiqadi. Jadvalning sonli qiymatlari o'z holicha qoladi.
- Brokerning rasmiy yuridik nomlari va identifikatorlarni tarjimada o'zgartirmaslik ko'rsatmasi mavjud; model tarjimasini Render'da haqiqiy so'rov bilan tekshirish tavsiya etiladi.
- Saqlanayotgan chat tarixi faqat shu brauzer tabining `sessionStorage` qismida mavjud. Boshqa brauzer/inkognito sessiyada avvalgi chatlar mavjud bo'lmaydi.

## Fayllar
- `index.html` — tilga mos qayta render + natijalarni keshlash
- `app.py` — POST `/api/translate` endpoint
- `translation.py` — lug'at, Gemini tarjima va sonlar yaxlitligini tekshirish

## Lokal tekshiruv
111/111 avtomatik test; Node.js sintaksis tekshiruvi o'tdi. Real Gemini va Render end-to-end tekshirilmadi.
