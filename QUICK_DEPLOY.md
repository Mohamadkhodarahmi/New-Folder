# ⚡ راهنمای سریع دیپلوی روی لیارا

## 🚀 3 قدم ساده

### 1️⃣ ایجاد اپلیکیشن در لیارا

```
1. وارد داشبورد لیارا شوید
2. Create New App → نام: wewewewe
3. Type: Worker
4. Location: Germany 🇩🇪
```

### 2️⃣ تنظیم متغیرهای محیطی

در داشبورد لیارا → Environment Variables → اضافه کنید:

```
TELEGRAM_BOT_TOKEN = توکن ربات تلگرام (از @BotFather)
USE_REAL_DATA = true
EXCHANGE_NAME = binance
```

### 3️⃣ آپلود کد

```bash
# روش 1: Git
git init
git add .
git commit -m "Deploy to Liara"
git remote add liara git@liara.ir:USERNAME/wewewewe.git
git push liara main

# روش 2: CLI
liara deploy --app wewewewe
```

---

## ✅ تست

در تلگرام ربات را باز کنید و بنویسید:
```
/start
```

اگر پاسخ داد، همه چیز آماده است! 🎉

---

## 📝 نکته مهم

فایل `liara.json` از قبل تنظیم شده و لوکیشن روی **آلمان** است.

---

## 🆘 مشکل؟

لاگ‌ها را بررسی کنید:
```bash
liara logs --app wewewewe
```

