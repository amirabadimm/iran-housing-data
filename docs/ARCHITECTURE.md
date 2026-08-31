# معماری مخزن

## محور موضوعی

```text
datasets/
├── housing_market/              بازار مسکن
│   ├── residential_sales/       معاملات خرید و فروش
│   ├── rent/                    اجاره‌بها
│   └── land/                    زمین
├── housing_supply/              عرضه مسکن
│   ├── building_permits/        پروانه‌های ساختمانی
│   ├── construction_starts/     شروع ساخت
│   └── construction_completions/ تکمیل ساختمان
├── construction_costs/          هزینه ساخت
├── housing_investment/          سرمایه‌گذاری مسکن
├── housing_finance/             تأمین مالی مسکن
├── capital_markets/             بازار سرمایه مرتبط
└── macroeconomic_environment/   محیط کلان
    ├── liquidity/               نقدینگی
    ├── inflation/               تورم
    ├── exchange_rate/           نرخ ارز
    ├── interest_rates/          نرخ‌های سود
    ├── unemployment/            بیکاری
    └── gdp/                     تولید ناخالص داخلی
```

منبع، شاخه اصلی نیست. برای مثال آمار مشابه بانک مرکزی و مرکز آمار دو dataset_id مستقل دارند، در `standardized` جدا می‌مانند و تنها با تعریف صریح روش تطبیق در `curated` ترکیب می‌شوند.

## لایه‌های داده

1. `incoming`: محل موقت فایل دستی یا تازه‌دریافت‌شده؛ قابل اتکا نیست.
2. `raw`: snapshot ثبت‌شده و تغییرناپذیر از فایل اصلی.
3. `standardized`: قالب یکنواخت، بدون ادغام مفهومی منابع مختلف.
4. `curated`: داده معتبر و پژوهش‌پذیر با قواعد مستند.
5. `marts`: مدل مصرفی، از جمله مدل ستاره‌ای Power BI.
6. `staging`: خروجی موقت هر run پیش از انتشار اتمی.

## واحد استقلال

هر مجموعه‌داده یک بسته مستقل در `datasets/<domain>/<topic>/<dataset_id>/` است و حداقل `dataset.yml`، `README.fa.md` و `schema.yml` دارد. کد فقط زمانی افزوده می‌شود که فایل واقعی و روش پردازش مشخص باشد.

چرخه وضعیت: `discovered → downloaded → inspected → registered → validated → standardized → published → monitored`.
