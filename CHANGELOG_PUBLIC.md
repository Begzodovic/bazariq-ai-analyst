# Hakamlarga ochiq demo uchun o‘zgarishlar

- Login/parol majburiyati butunlay olib tashlandi.
- Gemini API kaliti faqat server Environment’da; frontendga berilmaydi.
- Public so‘rovlar uchun 30/minut server-wide limit, 3 parallel so‘rov cheklovi.
- `uzex.db.gz` dan avtomatik chiqarish — GitHub 100 MB fayl chekloviga moslash.
- Render Starter doimiy server (pullik); muqobil Free da cold start kechikishi mumkin.
- 25 s AI timeout, FAST=1, murakkab second-pass audit default 0; mavjud lokal semantik SQL tekshiruvlari saqlangan.
- HTTP 422/503 ichki sabablari butunlay bartaraf etilgan deb hisoblanmaydi; real Gemini bilan regression benchmark talab qilinadi.
