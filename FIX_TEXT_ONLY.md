# BazarIQ — matn/jadval formatini hurmat qilish

- `jadval tuzma`, `faqat matn shaklida`, `без таблицы`, `только текстом` bo‘lsa API `display_format=text` qaytaradi.
- Backend natijani mavjud SQL qatorlaridan o‘zbek/rus tilida matn qilib yozadi; yangi raqam to‘qimaydi.
- Frontend `display_format=text` da HTML jadvalni yashiradi; SQL va manba tekshiruvi qoladi.
- Oddiy so‘rovlarda jadval odatdagidek ko‘rsatiladi.
- GitHub'da `analyst.py` va `index.html` ni yangilang; so‘ng Render deploy.
- Ushbu o‘zgarish boshqa SQL/AI xatolarini avtomatik tuzatmaydi.
