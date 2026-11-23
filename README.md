
# 🎵 MusicRoyalty
### Blockchain-Based Music Royalty Management System

MusicRoyalty adalah aplikasi berbasis blockchain yang dirancang untuk membantu pencatatan karya musik, pelacakan penggunaan musik, serta pengelolaan distribusi dan pembayaran royalti secara transparan.

Aplikasi ini menggunakan teknologi **Smart Contract** untuk mencatat aktivitas dan memproses transaksi royalti melalui jaringan blockchain lokal. Dengan integrasi MetaMask, pengguna dapat melakukan konfirmasi transaksi secara langsung melalui wallet.

---

## 📌 Fitur Utama

### 1. Dashboard
- Menampilkan jumlah karya musik yang terdaftar.
- Menampilkan akumulasi total royalti.
- Menampilkan jumlah pencipta musik.
- Memantau status blockchain dan smart contract.
- Visualisasi distribusi status karya dan royalti.

### 2. Music Catalog
- Menampilkan daftar karya musik yang terdaftar.
- Pencarian berdasarkan judul, Batch ID, dan jenis transaksi.
- Filter berdasarkan status karya.
- Tampilan data dalam bentuk tabel atau kartu.
- Ekspor data katalog ke format CSV.

### 3. Register Music
- Mendaftarkan karya musik baru.
- Membuat Music Batch dengan ID otomatis.
- Mencatat penggunaan musik.
- Menghitung hash file audio menggunakan SHA-256 sebagai informasi verifikasi file.

### 4. Music Detail
- Menampilkan informasi detail karya musik.
- Menampilkan pemilik hak cipta.
- Menampilkan total royalti.
- Menampilkan persentase pembagian royalti.
- Menampilkan riwayat aktivitas karya.

### 5. Royalty Distribution
- Simulasi pembagian royalti.
- Proses distribusi royalti melalui smart contract.
- Proses pembayaran royalti menggunakan ETH.
- Konfirmasi transaksi melalui MetaMask.

### 6. Royalty History
- Menampilkan riwayat aktivitas blockchain.
- Menampilkan waktu aktivitas.
- Menampilkan alamat wallet pelaku transaksi.
- Filter riwayat berdasarkan Music Batch.

### 7. Wallet & Transaction
- Menghubungkan wallet MetaMask.
- Menampilkan alamat wallet.
- Menampilkan saldo ETH.
- Mengidentifikasi peran akun.
- Memantau riwayat transaksi dan status konfirmasi.

---

## ⚙️ Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| Streamlit | Framework antarmuka aplikasi |
| Solidity | Bahasa pemrograman Smart Contract |
| Hardhat | Pengembangan dan pengujian blockchain lokal |
| Web3.py | Komunikasi Python dengan blockchain |
| MetaMask | Wallet dan konfirmasi transaksi |
| Plotly | Visualisasi data |
| HTML, CSS, JavaScript | Komponen antarmuka dan integrasi wallet |
| Ethereum | Ekosistem blockchain |

---

## 💰 Skema Pembagian Royalti

Sistem menggunakan pembagian persentase royalti kepada empat pihak:

| Pihak | Persentase |
|---|---:|
| Kreator | 60% |
| Produser | 20% |
| Penulis Lagu | 15% |
| Platform Musik | 5% |
| **Total** | **100%** |

Pembagian royalti dilakukan berdasarkan persentase yang telah ditentukan dalam aplikasi dan smart contract.

---

## 📊 Status Karya Musik

Setiap karya musik memiliki status yang menunjukkan tahapan pengelolaannya.

| Status | Keterangan |
|---|---|
| CREATED | Karya musik berhasil didaftarkan |
| USED | Karya musik telah dicatat penggunaannya |
| DISTRIBUTED | Royalti telah didistribusikan |
| COMPLETED | Proses pembayaran royalti telah diselesaikan |

---

## 📁 Struktur Project

Struktur utama project:

```text
MusicRoyalty/
│
├── app.py
│
├── contracts/
│   └── MusicRoyalty.sol
│
├── artifacts/
│   └── contracts/
│       └── MusicRoyalty.sol/
│           └── MusicRoyalty.json
│
├── deployment.json
│
├── package.json
│
├── hardhat.config.js
│
└── README.md
```

**Catatan:** Struktur di atas merupakan gambaran file utama berdasarkan kebutuhan aplikasi. File konfigurasi dan direktori lain dapat disesuaikan dengan struktur project yang sebenarnya.

---

## 🚀 Instalasi dan Menjalankan Project

### 1. Clone Repository

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
```

Masuk ke direktori project:

```bash
cd MusicRoyalty
```

### 2. Persiapkan Python Environment

Buat virtual environment:

```bash
python -m venv venv
```

Aktifkan virtual environment.

Windows:

```bash
venv\Scripts\activate
```

Install dependency:

```bash
pip install streamlit web3 plotly
```

### 3. Persiapkan Hardhat

Pastikan Node.js dan npm sudah terinstal.

Install dependency project:

```bash
npm install
```

Jalankan jaringan blockchain lokal:

```bash
npx hardhat node
```

Hardhat akan menyediakan jaringan lokal dengan RPC:

```text
http://127.0.0.1:8545
```

### 4. Deploy Smart Contract

Deploy smart contract `MusicRoyalty.sol` ke jaringan Hardhat Local menggunakan script deployment yang tersedia dalam project.

Setelah deployment berhasil, simpan alamat smart contract ke dalam file `deployment.json`.

Format:

```json
{
  "contractAddress": "ALAMAT_SMART_CONTRACT"
}
```

Pastikan ABI tersedia pada:

```text
artifacts/contracts/MusicRoyalty.sol/MusicRoyalty.json
```

### 5. Konfigurasi MetaMask

Tambahkan jaringan Hardhat Local ke MetaMask.

| Konfigurasi | Nilai |
|---|---|
| Network Name | Hardhat Local |
| RPC URL | http://127.0.0.1:8545 |
| Chain ID | 31337 |
| Currency Symbol | ETH |

Gunakan akun Hardhat yang sesuai dengan peran Kreator dan Platform Musik.

### 6. Jalankan Aplikasi

Buka terminal baru, aktifkan virtual environment jika belum aktif, lalu jalankan:

```bash
streamlit run app.py
```

Aplikasi dapat diakses melalui browser pada alamat lokal yang ditampilkan oleh Streamlit.

---

## 🔐 Hak Akses Pengguna

Aplikasi mengenali peran akun berdasarkan alamat wallet yang terdaftar pada smart contract.

| Peran | Hak Akses |
|---|---|
| Kreator | Mendaftarkan karya musik |
| Platform Musik | Melakukan distribusi dan pembayaran royalti |
| Akun Lain | Mengakses informasi sesuai fungsi aplikasi |

Setiap transaksi yang membutuhkan otorisasi harus dikonfirmasi melalui MetaMask.

---

## ⚠️ Catatan Penggunaan

1. Hardhat Node harus tetap berjalan selama aplikasi digunakan.
2. MetaMask harus terhubung dengan jaringan Hardhat Local.
3. Smart contract harus sudah di-deploy sebelum aplikasi dijalankan.
4. File `deployment.json` dan ABI harus tersedia pada lokasi yang sesuai.
5. Transaksi blockchain memerlukan konfirmasi dari wallet.
6. Hash SHA-256 file audio dihitung oleh aplikasi, tetapi tidak disimpan oleh fungsi `createBatch` pada smart contract.

---

## 🎯 Tujuan Project

Project ini dikembangkan sebagai implementasi pemanfaatan teknologi blockchain dalam pengelolaan hak cipta dan royalti musik.

Melalui smart contract, sistem diharapkan dapat memberikan transparansi dalam pencatatan penggunaan karya, distribusi royalti, serta proses pembayaran kepada pihak-pihak yang memiliki hak atas karya musik.

---

**MusicRoyalty — Transparency, Trust, and Fairness in Music Royalty Distribution.** 🎵
