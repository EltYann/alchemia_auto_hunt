# Alchemia Story Auto Hunt

Sistem auto hunting monster untuk Alchemia Story.
Jalan di Termux Android via ADB wireless.

## Flow Kerja
1. Screenshot layar
2. Detect monster (template matching)
3. Deketin monster (tap arah monster)
4. Game auto masuk combat + auto attack
5. Monster mati → drop muncul
6. Tap OK buat tutup dialog drop
7. Cari monster baru → ulangi

## Fitur
- Deteksi monster via template matching
- Auto approach monster (ga perlu tap monster)
- Auto tap OK saat drop muncul
- Anti-detection (random delay + jitter)
- Memory posisi monster (makin lama makin pinter)
- Multi template support (bisa detect banyak jenis monster)

## Requirements
- Android 11+ (wireless debugging)
- Termux (F-Droid)
- Python 3.10+
- OpenCV
- ADB tools

## Setup Termux
```bash
pkg update && pkg upgrade -y
pkg install python python-pip android-tools opencv-python tesseract
pip install numpy pillow pytesseract pyyaml
