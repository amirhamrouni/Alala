# MoneyPrinter Mobile Gateway

Gateway بين Telegram/HTTP وMoneyPrinterTurbo مع queue متسلسلة، job_id مستقل، dedupe، persistence، ومتابعة تلقائية للنتيجة.

## Colab الموصى به

استعمل:

`docs/MoneyPrinterTurbo.ipynb`

النسخة الحالية تشغل:

- MoneyPrinterTurbo WebUI على 8501.
- MoneyPrinter API على 8090.
- Arabic RTL patch قبل تشغيل السيرفر.
- `DejaVuSans.ttf` من نظام Colab داخل `resource/fonts`.
- `arabic-reshaper` + `python-bidi` لربط الحروف وترتيب RTL.
- ngrok token من Colab Secrets باسم `NGROK_AUTHTOKEN` بدل تخزينه في GitHub.

## Gateway

```bash
cp .env.example .env
docker compose up -d --build
```

إن كان Gateway في نفس الجهاز/Colab:

```env
MONEYPRINTER_BASE_URL=http://127.0.0.1:8090
```

إن كان خارج Colab استعمل قيمة `API_BASE` التي تطبعها خلية Colab.

## إنشاء فيديو

```bash
curl -X POST http://localhost:8000/make-video \
  -H "Content-Type: application/json" \
  -d '{"topic":"ارقام الهجرة غير الشرعية في تونس","video_language":"ar"}'
```

الرد يعطي `job_id` وليس task_id الخام.

تابع الحالة:

```bash
curl http://localhost:8000/jobs/JOB_ID
```

المراحل:

```text
queued -> submitting -> rendering -> ready | failed
```

`/tasks/{task_id}` مازال موجوداً فقط لفحص MoneyPrinter task الخام.

## Telegram

ضع في `.env`:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_CHAT_IDS=
```

ثم ثبت webhook بعد نشر Gateway على HTTPS:

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://YOUR_GATEWAY_DOMAIN/telegram/webhook"
```

مثال:

```text
اعمل فيديو عن تطور الذكاء الاصطناعي في 2026
```

كل رسالة تحصل على job_id مستقل. الطلب المطابق خلال فترة `DEDUPE_MINUTES` لا ينشئ فيديو مكرر.

## التخزين

`docker-compose.yml` يربط volume دائم إلى `/data`، وحالة المهام محفوظة في:

```text
/data/jobs.json
```

بعد إعادة تشغيل Gateway، المهام غير المنتهية يعاد إدخالها إلى queue وتكمل المتابعة.

## العربية

الإصلاح الحقيقي موجود في rendering نفسه، وليس في Telegram:

```text
Arabic font glyphs
+ Arabic shaping
+ RTL bidi ordering
+ UTF-8 subtitles
```

السكريبت:

```text
moneyprinter-mobile-gateway/scripts/patch_moneyprinter_arabic.py
```

هو idempotent ويمكن تشغيله أكثر من مرة.

## أمن المفاتيح

لا تضع `TELEGRAM_BOT_TOKEN` أو `NGROK_AUTHTOKEN` داخل notebook أو repository. استعمل `.env`/GitHub Secrets/Colab Secrets فقط.
