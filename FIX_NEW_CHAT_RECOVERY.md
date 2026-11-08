# BazarIQ — mustaqil savollar va yangi chat tavsiyasi

## Yangilangan fayllar
- `analyst.py`: mustaqil savollarga eski chat filtrlarini qo‘shmaydi; davomiy «shu 5 ta broker» kabi savollarda mavjud suhbatni saqlaydi. Xato eski chatda yuz bersa, `suggest_new_chat` signalini yuboradi.
- `index.html`: xatoda «Yangi chatda sinash / Попробовать в новом чате» tugmasini ko‘rsatadi. Tugma yangi chat ochadi va oxirgi savolni yozish maydoniga ko‘chiradi; foydalanuvchi tasdiqlamasdan savol yuborilmaydi.
- `tests/test_context_recovery.py`: eski chat filtrlari va davomiy savollar uchun regression testlar.

## GitHub + Render
1. `analyst.py` va `index.html` fayllarini GitHub repository asosiy papkasida almashtiring.
2. Commit changes bosing.
3. Render → Manual Deploy → Deploy latest commit.
4. Eski chatda 2025-yil savolidan keyin mustaqil 2024-yil TOP-5 savolini sinang.
5. Keyin «shu 5 ta broker» savolini bering; oldingi ro‘yxat o‘zgarmasligini tekshiring.

## Cheklovlar
- Bu tuzatish SQL, Gemini yoki server xatosini ma’lumot yo‘q deb yashirmaydi.
- Kutilmagan texnik xatoda yangi chat tavsiyasi faqat qo‘shimcha vosita, davolovchi yechim emas.
- Agar Render'da eski JS versiyasi ko‘rinayotgan bo‘lsa, Ctrl+F5 bosing.
- `.env` va API kalitlarni GitHub'ga joylamang.
