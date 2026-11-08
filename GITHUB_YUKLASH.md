# GitHub upload — BazarIQ

GitHub brauzerida 25 MB dan katta bitta faylni yuklab bo‘lmaydi. Bu papkada bazaning 4 qismi bor:

- `uzex.db.gz.part01` — 12 MB
- `uzex.db.gz.part02` — 12 MB
- `uzex.db.gz.part03` — 12 MB
- `uzex.db.gz.part04` — 2.64 MB

Barcha fayllarni (jumladan 4 ta partni) repositoryning **ildiz** qismiga upload qiling. ZIP faylning o‘zini yuklamang. `uzex.db` ni ham yuklamang. `.env` va maxfiy API kalitlarini yubormang.

Render serveri `db_bootstrap.py` orqali 4 qismni tartib bilan birlashtirib, 232 MB SQLite bazasini `/tmp`ga ochadi. Render → New → Blueprint → GitHub repo tanlang. `GEMINI_API_KEY` Render Environment'da saqlansin.

Agar GitHub repoda eski `uzex.db` yoki `uzex.db.gz` bo‘lsa, ularni o‘chiring, aks holda eski versiya ishga tushishi mumkin.
