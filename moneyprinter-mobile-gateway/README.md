# MoneyPrinter Mobile Gateway

خدمة صغيرة تربط هاتفك بـ MoneyPrinterTurbo. ترسل موضوع الفيديو من Telegram أو HTTP، وهي تنشئ مهمة في MoneyPrinterTurbo وتتابعها في الخلفية حتى يرجع رابط الفيديو.

## التشغيل السريع

1. انسخ `.env.example` إلى `.env`.
2. عدل `MONEYPRINTER_BASE_URL` إلى رابط MoneyPrinterTurbo API. إذا كان نفس رابط ngrok الحالي خليه كما هو.
3. شغل الخدمة:

```bash
docker compose up -d --build
```

4. جرّب من الهاتف أو curl:

```bash
curl -X POST http://localhost:8000/make-video \
  -H "Content-Type: application/json" \
  -d '{"topic":"اعملي فيديو عن افضل ادوات الذكاء الاصطناعي للطلاب"}'
```

تابع المهمة:

```bash
curl http://localhost:8000/tasks/TASK_ID
```

## Telegram

1. أنشئ bot من BotFather وخذ `TELEGRAM_BOT_TOKEN`.
2. ضع التوكن في `.env`.
3. بعد نشر الخدمة على رابط HTTPS، ثبت webhook:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://YOUR_GATEWAY_DOMAIN/telegram/webhook"
```

بعدها ابعث للبوت:

```text
اعملي فيديو عن كيف يغير الذكاء الاصطناعي حياة الناس
```

## GitHub Deploy

ارفع هذا المجلد إلى GitHub، ثم أضف secrets:

- `SSH_HOST`
- `SSH_USER`
- `SSH_KEY`
- `APP_DIR`

كل push إلى `main` يشغل `docker compose up -d --build` على السيرفر.

## ملاحظات مهمة

- MoneyPrinterTurbo نفسه لازم يكون شغال وفيه مفاتيح LLM/TTS/stock footage مضبوطة.
- الـ API الرسمي يستعمل `POST /api/v1/videos` و `GET /api/v1/tasks/{task_id}`.
- ngrok المجاني يصلح للتجربة، لكن للإنتاج استعمل VPS أو Cloudflare Tunnel أو Render/Railway.
