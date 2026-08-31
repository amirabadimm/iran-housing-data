# سامانه پژوهش و پایش داده‌های مسکن

این مخزن برای گردآوری کنترل‌شده، نگهداری، استانداردسازی، پژوهش و پایش داده‌های بازار مسکن ایران طراحی شده است. ساختار اصلی **موضوع‌محور** است؛ سازمان تولیدکننده، نشانی صفحه منبع و لینک دانلود در شناسنامه هر مجموعه‌داده ثبت می‌شوند.

## اصول

- هر فایل ورودی پیش از پردازش با منبع، تاریخ دریافت و checksum ثبت می‌شود.
- فایل خام تغییر نمی‌کند و نسخه‌های جدید جای نسخه‌های قبلی را نمی‌گیرند.
- داده‌های مشابه از منابع مختلف تا لایه استانداردشده جدا نگه داشته می‌شوند.
- خروجی جدید ابتدا در staging ساخته و آزموده می‌شود و سپس به‌صورت اتمی منتشر می‌شود.
- اجرای مجدد روی ورودی یکسان نباید رکورد تکراری یا خروجی متفاوت بسازد.
- Power BI فقط از `data/curated/` و `data/marts/power_bi/` تغذیه می‌شود.

## نقشه مخزن

- `datasets/`: فهرست موضوعات و بسته‌های مستقل مجموعه‌داده
- `data/`: فایل‌های ورودی، خام، استانداردشده، نهایی و دیتامارت‌ها
- `metadata/`: رجیستری داده، منبع، فایل، متغیر، کیفیت و اجرای به‌روزرسانی
- `pipelines/`: کدهای واقعی دریافت، استانداردسازی، اعتبارسنجی و انتشار
- `research/`: پرسش‌ها، روش‌ها، ادبیات و نوت‌بوک‌های پژوهشی
- `dashboards/power_bi/`: مستندات مدل و داشبورد Power BI
- `outputs/`: جدول، نمودار و گزارش قابل تحویل
- `templates/dataset/`: الگوی ساخت بسته یک مجموعه‌داده جدید

## ورود اولین فایل

1. فایل را بدون تغییر در `data/incoming/` قرار دهید.
2. منبع و تعریف آن را بررسی و در رجیستری‌ها ثبت کنید.
3. نسخه خام را با مسیر موضوع/شناسه داده/تاریخ snapshot نگهداری کنید.
4. فقط در صورت وجود هدف روشن، تبدیل و اعتبارسنجی بسازید.
5. پس از قبولی کنترل کیفیت، خروجی curated یا mart را منتشر کنید.

جزئیات در [معماری](docs/ARCHITECTURE.md)، [قرارداد مجموعه‌داده](docs/DATASET_CONTRACT.md) و [پروتکل به‌روزرسانی](docs/UPDATE_PROTOCOL.md) آمده است.
## Development environment

Python 3.11 or newer is required. This repository shares `E:\\Finenv` with the sibling
`E:\\Work` empirical-research repository. From `E:\\Housing` in PowerShell:

```powershell
py -m venv ..\Finenv
..\Finenv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

VS Code is configured to use the shared environment automatically. Keep repository-specific direct
dependencies in `requirements.txt`; do not commit virtual environments, caches, or credentials.
