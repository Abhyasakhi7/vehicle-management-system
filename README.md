# Vehicle Management System

Aplikasi web untuk mengelola data kendaraan, riwayat servis, pengisian bahan bakar, pengeluaran, dan pengingat perawatan. Dibangun dengan Django, Django REST Framework, PostgreSQL, dan antarmuka web responsif.

## Fitur

- Registrasi, login, dan logout dengan autentikasi token.
- CRUD kendaraan dengan dukungan beberapa kendaraan per pengguna.
- Pencatatan riwayat servis (maintenance) beserta jadwal servis berikutnya.
- Pencatatan pengisian BBM dengan total biaya yang dihitung otomatis.
- Pencatatan pengeluaran kendaraan (pajak, asuransi, parkir, tol, cuci, dll.).
- Reminder servis berdasarkan tanggal dan/atau odometer.
- Dashboard berisi ringkasan biaya, grafik 6 bulan, aktivitas terbaru, dan servis mendatang.
- Isolasi data: pengguna hanya dapat mengakses data kendaraannya sendiri.
- REST API dengan validasi, filter, pencarian, pengurutan, dan pagination.
- Antarmuka web responsif dengan tema gelap dan aksen oranye.

## Teknologi

| Komponen | Versi |
| --- | --- |
| Python | 3.14 (diuji pada 3.14.9) |
| Django | 6.1.3 |
| Django REST Framework | 3.18.3 |
| django-filter | 26.2 |
| PostgreSQL | 14+ |
| psycopg | 3.3.8 |
| Bootstrap | 5.3.3 (CDN) |
| JavaScript | Vanilla JS |

## Struktur Proyek

```text
vehicle-management-system/
├── apps/
│   ├── accounts/       # Registrasi, login, logout, profil
│   ├── vehicles/       # CRUD kendaraan
│   ├── maintenance/    # Riwayat servis
│   ├── fuel/           # Riwayat pengisian BBM
│   ├── expenses/       # Pengeluaran kendaraan
│   ├── reminders/      # Pengingat perawatan
│   └── dashboard/      # Agregasi data dashboard
├── config/
│   ├── settings/       # base, development, production
│   └── urls.py         # Routing API dan halaman web
├── templates/          # Template halaman web
├── static/             # CSS dan JavaScript
├── manage.py
├── requirements.txt
└── .env.example
```

## Prasyarat

- Python 3.14
- PostgreSQL
- pip dan virtualenv (bawaan Python)

### Instalasi PostgreSQL (Arch/CachyOS)

```bash
sudo pacman -S postgresql
sudo systemctl enable --now postgresql
```

Buat database dan pengguna:

```bash
sudo -u postgres psql
```

```sql
CREATE USER vehicle_user WITH PASSWORD 'ganti_dengan_password_kuat';
CREATE DATABASE vehicle_db OWNER vehicle_user;
ALTER ROLE vehicle_user CREATEDB;
ALTER ROLE vehicle_user SET client_encoding TO 'utf8';
ALTER ROLE vehicle_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE vehicle_user SET timezone TO 'Asia/Jakarta';
\q
```

`ALTER ROLE ... CREATEDB` diperlukan agar Django dapat membuat database khusus saat menjalankan test.

## Instalasi

```bash
cd vehicle-management-system  # sesuaikan dengan lokasi proyek Anda

python -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Salin konfigurasi environment (lewati jika `.env` sudah ada):

```bash
cp .env.example .env
```

Buat `SECRET_KEY` acak:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Edit `.env` dan sesuaikan nilainya:

```env
DEBUG=True
SECRET_KEY=hasil_dari_perintah_di_atas
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=vehicle_db
DB_USER=vehicle_user
DB_PASSWORD=password_database_anda
DB_HOST=127.0.0.1
DB_PORT=5432
```

`.env` sudah tercantum di `.gitignore` sehingga tidak akan ikut ter-commit.

Jalankan migrasi:

```bash
.venv/bin/python manage.py migrate
```

Opsional, buat akun admin untuk Django Admin:

```bash
.venv/bin/python manage.py createsuperuser
```

## Menjalankan Aplikasi

```bash
.venv/bin/python manage.py runserver
```

Buka browser:

- Aplikasi: <http://127.0.0.1:8000/>
- Django Admin: <http://127.0.0.1:8000/admin/> (jika sudah membuat superuser)

Jika port 8000 sedang digunakan:

```bash
.venv/bin/python manage.py runserver 8001
```

Hentikan server dengan `Ctrl+C`.

## Cara Penggunaan

1. Buka halaman **Daftar** dan buat akun baru, atau login jika sudah punya akun.
2. Tambahkan kendaraan melalui menu **My Vehicles**.
3. Catat servis, pengisian BBM, pengeluaran, dan reminder melalui menu masing-masing.
4. Pantau ringkasan biaya dan aktivitas di halaman **Dashboard**.
5. Gunakan filter tanggal pada dashboard untuk melihat periode tertentu.

## Dokumentasi API

Base URL: `http://127.0.0.1:8000/api/v1/`

Autentikasi menggunakan token. Sertakan header berikut pada setiap request yang membutuhkan login:

```http
Authorization: Token <token>
```

### Endpoint Autentikasi

| Method | Endpoint | Deskripsi |
| --- | --- | --- |
| POST | `/auth/register/` | Registrasi pengguna baru |
| POST | `/auth/login/` | Login dengan username atau email |
| POST | `/auth/logout/` | Logout dan hapus token |
| GET | `/auth/me/` | Data pengguna yang sedang login |

Contoh login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"username_anda","password":"password_anda"}'
```

Response:

```json
{
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "user": {
    "id": 1,
    "username": "username_anda",
    "email": "email@example.com",
    "first_name": "",
    "last_name": "",
    "date_joined": "2026-11-13T08:00:00+07:00"
  }
}
```

### Endpoint Data

| Resource | Endpoint | Filter | Pencarian | Ordering |
| --- | --- | --- | --- | --- |
| Kendaraan | `/vehicles/` | `vehicle_type`, `fuel_type`, `transmission`, `year`, `brand` | `search` | `name`, `brand`, `year`, `mileage`, `created_at` |
| Servis | `/maintenance/` | `vehicle`, `service_type`, `service_date` | `search` | `service_date`, `cost`, `mileage`, `created_at` |
| BBM | `/fuel/` | `vehicle`, `is_full_tank`, `date` | `search` | `date`, `mileage`, `total_cost`, `created_at` |
| Pengeluaran | `/expenses/` | `vehicle`, `category`, `date` | `search` | `date`, `amount`, `created_at` |
| Reminder | `/reminders/` | `vehicle`, `status`, `due_date` | `search` | `due_date`, `due_mileage`, `created_at` |

Semua resource mendukung operasi `GET`, `POST`, `PUT`, `PATCH`, dan `DELETE`.

Contoh request dengan token:

```bash
curl http://127.0.0.1:8000/api/v1/vehicles/ \
  -H "Authorization: Token <token>"
```

Contoh filter dan pencarian:

```bash
curl "http://127.0.0.1:8000/api/v1/maintenance/?vehicle=1&service_type=OIL_CHANGE&search=oli" \
  -H "Authorization: Token <token>"
```

Pagination menggunakan parameter `page` dengan ukuran 20 data per halaman:

```bash
curl "http://127.0.0.1:8000/api/v1/vehicles/?page=2" \
  -H "Authorization: Token <token>"
```

### Endpoint Dashboard

| Method | Endpoint | Deskripsi |
| --- | --- | --- |
| GET | `/dashboard/` | Ringkasan data dashboard |

Parameter opsional:

- `start_date` — format `YYYY-MM-DD`
- `end_date` — format `YYYY-MM-DD`

Contoh:

```bash
curl "http://127.0.0.1:8000/api/v1/dashboard/?start_date=2026-01-01&end_date=2026-12-31" \
  -H "Authorization: Token <token>"
```

Response berisi `total_vehicles`, `total_cost`, `cost_breakdown`, `total_distance`, `recent_activity`, `upcoming_maintenance`, dan `monthly_expenses`.

## Menjalankan Test

```bash
.venv/bin/python manage.py test
```

Saat ini terdapat 107 automated test yang mencakup autentikasi, CRUD, validasi, permission, isolasi data, filter, pencarian, ordering, dan dashboard.

Menjalankan test untuk satu aplikasi:

```bash
.venv/bin/python manage.py test apps.reminders
```

Test menggunakan database PostgreSQL terpisah dan membutuhkan hak `CREATEDB` pada user database.

## Pengaturan Development dan Production

- `manage.py` menggunakan `config.settings.development` secara default.
- `config/wsgi.py` dan `config/asgi.py` menggunakan `config.settings.production`.
- Pada production, `DEBUG=False` dan konfigurasi keamanan HTTPS diaktifkan. Pastikan `SECRET_KEY`, `ALLOWED_HOSTS`, dan kredensial database diatur melalui environment.

## Catatan

- Bootstrap dan Google Fonts dimuat melalui CDN sehingga membutuhkan koneksi internet. CSS dan JavaScript aplikasi sendiri tetap tersedia secara lokal.
- Token autentikasi disimpan di `localStorage` untuk kebutuhan MVP. Untuk production, pertimbangkan mekanisme penyimpanan token yang lebih aman.
- Docker dan deployment belum disertakan pada versi ini.
- Jangan commit file `.env` atau kredensial asli ke repository.
