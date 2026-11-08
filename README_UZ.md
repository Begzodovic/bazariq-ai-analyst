# BazarIQ

O‘zbekcha va ruscha savolni SQLite so‘roviga aylantiradigan mahalliy veb-ilova. Arxivda xakatonning tayyor o‘quv reyestri bor. Kompaniyalar, narxlar va kurslar ushbu reyestr uchun yaratilgan.

## Oldingi versiyadan yangilash

ZIPni yangi papkaga oching. Eski serverni Ctrl+C bilan to‘xtating. O‘z kompyuteringizdagi ishlaydigan `.env` faylini yangi papkaga ko‘chiring. Kalitni arxivga joylamang. Yangi papkada `py app.py` buyrug‘ini bajaring.

Ikki tilli chatda suhbatni chap paneldan tanlaysiz. Telefonda menyu tugmasini bosing. Yangi chat alohida kontekst ochadi. Joriy suhbatlar brauzer tabining sessionStorage xotirasida saqlanadi. Keyingi savol uchun oxirgi uchta tegishli savol-javob kontekst sifatida yuboriladi; natijalar yana SQLite orqali olinadi. “Hisoblash usuli va SQL” bo‘limida hisobni tekshirish mumkin. Ilova faqat so‘rov kutilayotgan vaqtda harakatlanuvchi indikatorni ko‘rsatadi.

## Windows’da ishga tushirish

1. ZIP ichidagilarni bitta papkaga to‘liq chiqaring. Shu papkada PowerShell oching. Windows uchun Python 3.12 yoki undan yangi, SQLite moduli bilan kerak. Versiyani `py -V` orqali tekshiring. Qo‘shimcha pip paketi talab qilinmaydi.
2. `Copy-Item .env.example .env` buyrug‘ini bir marta bajaring. Keyin `notepad .env` bilan oching.
3. `AI_PROVIDER` ni tanlang va mos kalitni o‘z kompyuteringizda kiriting. Fayl aynan `.env` bo‘lib saqlansin. Avvaldan PowerShell muhitida o‘rnatilgan o‘zgaruvchilar fayldan ustun turadi.
4. Model tanlash uchun `py app.py --list-models` ni bajaring. Ro‘yxatdan matnli chatni qo‘llaydigan, hisobingizga ochiq modelning aniq ID sini tegishli `*_MODEL` satriga yozing. Har bir model chat uchun yaroqli bo‘lavermaydi. Katalogga kirish cheklansa, provayder konsolidagi chat modeli ID sini yozib, keyingi buyruq bilan tekshiring.
5. `py app.py --check-provider` modelga kichik jonli so‘rov yuboradi. Model ID va `OK` chiqqach, `py app.py` ni bajaring. Brauzerda http://localhost:8000 ni oching. Serverni to‘xtatish uchun Ctrl+C. .env o‘zgarsa serverni qayta ishga tushiring.

| AI_PROVIDER | Kalit | Model |
| --- | --- | --- |
| groq | GROQ_API_KEY | GROQ_MODEL |
| xai | XAI_API_KEY | XAI_MODEL |
| gemini | GEMINI_API_KEY | GEMINI_MODEL |

Savol, sxema, qidiruv namunalari va qisqa natija parchasi tanlangan APIga yuboriladi. Kalit serverda saqlanadi. Interfeys 127.0.0.1 manzilida ishlaydi. Model javobi yoki ulanish muvaffaqiyatsiz bo‘lsa, ilova provayder nomi va xatosini ko‘rsatadi. 401 kalitga, 403 ruxsatga, 404 model yoki endpointga, 429 kvota yoki so‘rov tezligiga tegishli. Ayrim provayderlar model xatosiga 400 yoki 403 ham qaytaradi.

## Savoldan natijagacha

Ilova ishga tushganda SQLite sxemasini, ustun turlarini, kalitlarni, davr chegaralarini va haqiqiy kategoriya qiymatlarini o‘qiydi. columns.json asl CSV sarlavhalarini SQLite nomlariga bog‘laydi. REGISTER_UZ_RU.md faylida reyestr muallifining ma’lumot lug‘ati bor.

Model erkin savol uchun yangi SQL tuzadi. Zaruratda atama yoki nomzod qiymatlarni topish uchun ikki martagacha chegaralangan SELECT bajaradi. Muhim noaniqlik bo‘lsa savol qaytaradi. Interfeysda aniqlashtirishga yozilgan javob dastlabki savol bilan birga yuboriladi.

SQLite asl sxemada so‘rovni tayyorlaydi. Baza faqat o‘qish uchun ochiladi. SQLite authorizer faqat ma’lum jadvallar, SELECT va ruxsat berilgan funksiyalarga yo‘l beradi. Bir nechta SQL operatori, noma’lum ustun, yozish yoki tashqi faylni ulash rad etiladi. Asosiy SQL uchun 8 soniyalik, izlash uchun 4 soniyalik bajarilish chegarasi qo‘yilgan. Jadvalda ko‘pi bilan 100 qator chiqadi; ortiqcha qator bo‘lsa belgi ko‘rinadi. Bu agregat hisobidan oldin ma’lumotni kesmaydi.

Model ikkinchi chaqiruvda asl savol, o‘qilgan ustunlar, hisoblash usuli va SQL natijasining namunasini tekshiradi. Bitta sonli natija uchun qo‘shimcha nazorat SQL ham bajariladi. Butun sonlar aniq, haqiqiy sonlar kichik suzuvchi nuqta toleransi bilan solishtiriladi. Xatoga ikki martagacha tuzatish beriladi. Har ikki SQL bitta modeldan keladi, shuning uchun noto‘g‘ri talqin ikkala tekshiruvdan ham o‘tishi mumkin. Interfeysdagi raqam va jadval SQLite qaytargan satrlardan bevosita olinadi.

## Bazada tekshirilgan natijalar

| Tekshiruv | Natija |
| --- | ---: |
| Bitimlar | 500 000 |
| Shartnomalar | 6 616 |
| Ishtirokchilar | 14 392 |
| Brokerlar | 120 |
| Kurs yozuvlari | 1 765 |
| Bitim sanalari | 2022-01-03 — 2026-10-30 |
| 2025-yildagi bitimlar | 115 763 |

2026-yil qisman qamrab olingan. Bitimdagi region sotuvchi omboriga tegishli. Xaridor hududi uchun participants bilan xaridor STIR bo‘yicha bog‘lanadi. Miqdor lotlarda berilgan. O‘lchov birligidagi hajm miqdor va lot o‘lchamining ko‘paytmasi. Bitim summasi shartnoma valyutasida; USDni so‘mga aylantirishda bitim sanasidagi kurs olinadi.

2025-yil natijasini qo‘lda qayta tekshirish:

```sql
SELECT COUNT(*) FROM deals
WHERE day >= '2025-01-01' AND day < '2026-01-01';
```

## Sinov va hakamlar savollariga tayyorgarlik

```powershell
py -m unittest discover -s tests -v
py evaluate.py --seed 714 --report reference-local.json
py evaluate.py --live --seed 1105 --report evaluation-live.json
```

- Birinchi buyruq regressiya testlarini bajaradi. Model xatolari va rejalashtirish ketma-ketligi testlarda boshqariladi; SQLite hisoblari arxivdagi bazada bajariladi.
- Ikkinchisi javob beriladigan 11 turdagi savol uchun etalon SQLni alohida Python agregatsiyasi bilan solishtiradi. Uchta qo‘shimcha holat aniqlashtirish yoki ma’lumot yetishmasligini tekshiradi. Seed yil, oy, hudud, broker va reyting uzunligini tanlaydi. Standart seed bo‘yicha bajarilgan natijalar reference-check.json faylida.
- Uchinchi buyruq 14 holatning har birini o‘zbek va rus tilida haqiqiy provayderga beradi (28 savol). Avval kichik sinov uchun `--limit 2` qo‘shish mumkin. API xarajati tarifga bog‘liq. Etalon savollar va javoblar agentga uzatilmaydi.
- Hisobot javob tili va turi, aniq natija, qator/ustun tartibi, bajarilgan SQL qaytgan holatlar, qayta hisoblaganda jadval hamda raqamli javobning mosligi, median va p95 kechikishni o‘lchaydi. Pul yoki foiz ikki kasr xonasigacha so‘ralgan hollarda etalon shu aniqlikda. Bir xil sonni boshqa ustunlar bilan bergan javob ham qat’iy mezonda xato hisoblanishi mumkin. Izohning mazmuni va aniqlashtirish savolining sifatini inson alohida baholaydi. Jarayon tekshiruv muvaffaqiyatsiz bo‘lsa nolga teng bo‘lmagan chiqish kodi beradi.
- Topshirishdan oldin boshqa seed va o‘zingiz tuzgan qo‘shimcha savollar bilan jonli sinang. Etalon to‘plam modelning avval ko‘rilmagan barcha savollardagi aniqligini belgilamaydi.

## HTTP

GET /health baza davri, provayder, model, sozlanganlik va oxirgi muvaffaqiyatli model javobi holatini qaytaradi. POST /api/ask ga application/json shaklida {"question":"…","lang":"uz"} yuboriladi. lang interfeys tilidir; javob tili savoldan aniqlanadi. status qiymatlari ok, clarify, unavailable, error, provider_error. Muvaffaqiyatda rows, columns, source, sql, note va tegishli bo‘lsa check_sql keladi.

## 2026-11-05 yangilanishi — BazarIQ Fast

- `BAZARIQ_FAST=1` — standart rejim: model odatda **bir marta** SQL rejalashtiradi, so‘rov SQLite tomonidan tekshiriladi va bajariladi. Model qaytargan SQL xato bo‘lsa, cheklangan tuzatishlar bor. Bu tezroq, lekin har doim mustaqil semantik nazorat bermaydi. **Murakkab moliyaviy hisoblarni tekshirish uchun** `BAZARIQ_FAST=0` qo‘ying (eski model-auditor + nazorat SQL tartibi).
- Oddiy brokerlarning to‘liq ro‘yxati, brokerlar soni va reyestrdagi eng so‘nggi USD kursi kabi qat’iy aniqlanadigan so‘rovlar modelga yuborilmaydi, bazadan to‘g‘ridan-to‘g‘ri olinadi. Brokerlar ro‘yxatidagi barcha 120 qator ko‘rsatiladi. Aniqlashtirishlar yoki qo‘shimcha filtrlar bo‘lsa, universal SQL-agent ishlaydi.
- Matnning turlicha aytilishi uchun SQL-agent avvalgi ko‘rsatmalar va real jadval ustunlari asosida ishlaydi. Qidiruv katalogi ixchamlashtirildi; savolga tegishli haqiqiy mahsulot nomlari/kodlari yuboriladi. Topilmagan nomlar uchun model avval jadval ichidan `SELECT DISTINCT` bilan qidirishi mumkin. Savolni aniq tushunmasa, uydirma javob emas, aniqlashtirish qaytarishi lozim.
- Bir xil sodda savollar uchun cheklangan xotira keshi ishlatiladi. API so‘rovi vaqti `AI_TIMEOUT=20` orqali boshqariladi. Gemini'ning ba’zi OpenAI-compatible modellari `json_schema` formatini qabul qilmaydi: `GEMINI_JSON_SCHEMA=0` da modeldan JSON matn so‘raladi, javobdagi qo‘shimcha matnni ajratish ham qo‘llab-quvvatlanadi. Agar modelingiz `json_schema` ni aniq qo‘llasa, `1` qilib yoqing.
- Tezkor javoblar faqat reyestrdan olinadi. Internetdagi bugungi valyuta kurslari yoki reyestrda yo‘q faktlar chiqarilmaydi.

**Muhim:** Cheksiz savollarni 100% to‘g‘ri tushunadigan AI kafolati yo‘q. Hakamlar savollariga tayyorgarlik uchun `py evaluate.py --live --limit 2` dan boshlang, keyin savollarni to‘liq ruscha va o‘zbekcha sinang. API kaliti ZIPga kiritilmagan. `.env` faylini o‘zingiz yaratasiz yoki eski papkadan ko‘chirasiz.
