# BazarIQ — semantik aniqlik va 90 soniyalik ishlash chegarasi

## Nima yangilandi

- `semantic.py`: suhbatdan `years`, `region`, `region_type`, `selected_set`, `metric`, `comparison` holati qayta tiklanadi. Yangi savolda aniq berilgan filtr oldingisini almashtiradi.
- `index.html`: brauzer oldingi 12 turdan reja, haqiqiy mahsulot kodlari va strukturali holatni uzatadi. Yangi chatda kontekst alohida.
- Avvalgi TOP-N natijasining `hs_code` identifikatorlari qo‘shimcha qaytariladi. Keyingi savolda **o‘sha kodlarni** ishlatish va nol yozuvli mahsulotlarni ham `LEFT JOIN` bilan ko‘rsatish talab qilinadi.
- Broker ishtirokida sotuvchi va xaridor rolini ikkita alohida hisob yoki `UNION ALL` bilan qo‘shish tekshiriladi. Bitimlar soni broker roli ishtiroklariga teng emas.
- Sotuvchi/xaridor ro‘yxatdan o‘tgan hududi bitimning ombor hududidan alohida; rol talab qilinganda tegishli INN bilan `participants` jadvali ishlatilishi tekshiriladi.
- Sotuvchi + xaridor = jami arifmetik invariant tekshiriladi, mos kelmasa modelga tuzatish yuboriladi.
- Oldingi kurs so‘ralganda sanani ham chiqarish talab qilinadi. Kursning avvalgi mavjud yozuvi bilan avvalgi kalendar kun farqlanadi.
- Murakkab so‘rovlar uchun mustaqil audit **standart holatda yoqilgan**; oddiy savollar tezkor yo‘lda qoladi.
- Model tarmoq so‘rovlarining timeout'i umumiy **85 soniyalik** deadline bilan cheklanadi. Bu 90 soniya talabiga zaxira, ammo tashqi tarmoq yoki qurilma sharoitida mutlaq kafolat emas.
- 39 ta avtomatik regression testi muvaffaqiyatli o'tdi (32 ta oldingi + 7 ta yangi).

## Muhim chegaralar

- Ushbu tekshiruvlar ma'lum semantik xatolarni ushlaydi; barcha ehtimoliy tabiiy til savollariga to‘liq matematik kafolat bermaydi.
- Tashqi Groq/xAI/Gemini API bilan haqiqiy 8-test ketma-ketligini **jonli qayta o'tkazish amalga oshirilmagan** (kalitlar yo‘q). Baho yoki 90 soniya ichida 100% aniqlik tasdiqlanmagan.
- TOP-N kodlarini saqlash uchun model birinchi natijada `hs_code` ni qaytarishi kerak; nomsiz yoki kodsiz tasnifni orqadan taxmin qilish xavfsiz emas.
- Valyuta va mahsulotlarning har qanday noaniq ekvivalentliklari avtomatik birlashtirilmaydi; kerak bo‘lsa aniqlashtirish talab qilinadi.
- Reyestrdagi kurslarni ma'lum kun uchun alohida tekshirish lozim; 2026-10-30 bitim qamrovi kurslar jadvalining qamrovidan mustaqil.

## Ishga tushirish

1. ZIP arxivni oching.
2. `.env.example` ni `.env` ga nusxalang va faqat o‘zingizning API kalitingiz va faol model nomini kiriting.
3. `py app.py`, keyin `http://localhost:8000`.
4. Sinovlar: `py -m unittest discover -s tests -v`.

## Sozlamalar

- `BAZARIQ_FAST=1`: oddiy savollarga bitta AI chaqiruvi yoki lokal SQL.
- `BAZARIQ_AUDIT_COMPLEX=1`: reyting, broker, foiz, qiyoslash, o‘rtacha, valyuta, kurs va suhbatga bog‘liq savollar uchun qo‘shimcha mustaqil tekshiruv.
- `BAZARIQ_FAST=0`: barcha savollarga mustaqil audit; sekinroq.
- `AI_TIMEOUT=18`: har bir tashqi AI murojaati uchun maksimal soniya; umumiy limit **85 soniya**.

## Hackathon oldidan majburiy sinovlar

Bir xil brauzer suhbatida oldingi TOP-5 → o‘sha mahsulotlarning boshqa hududdagi summasi → oldingi/yanada avvalgi yil → foiz o‘zgarishi; alohida broker TOP-10 sotuvchi/xaridor/jami; brokerning faqat sotuvchi roli bilan Toshkentdagi ishtiroki; oxirgi va oldingi USD kursining **sanasi** sinovlarini 10 marta qaytaring. Har bir javobni raw SQL natijasi va oldingi filtrlar bilan solishtiring. Yakuniy hakamlar 8 ta testi uchun aynan savollar va kutilgan SQL yoki bazadagi qiymatlar kerak bo‘ladi.
