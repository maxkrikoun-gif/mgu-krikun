# Первый запуск на ГУ (krikun + RideTube)

## 1. Store

- Источник: **`maxkrikoun-gif/mgu-krikun`**, канал **ветка `main`** (не Releases).
- Токен GitHub в настройках Store, если репо private.
- База (из **других** уже стоящих источников): **mgu-deploy**, **mgu-python**, **mgu-render**, **mgu-uplink**, **idrive7-renderd**, **mgu-inputgate**.
- Из **mgu-krikun / main**: **jap-node22** → **krikun-xray** → остальное по таблице ниже.

| Порядок | Пакет |
|---------|--------|
| 1 | jap-node22 (первый запуск может скачать Node с nodejs.org) |
| 2 | krikun-xray, **Krikun: сеть** |
| 3 | jap-ridetube-d → **YouT** |
| 4 | jap-filmix-d → **FilmixProMax** |

После **mgu-inputgate** — перезапуск ГУ (если Store просит).

## 2. Xray

1. USB: `KRIKUN/xray.json` → импорт в **Krikun: сеть**.
2. **Запустить обход** (SOCKS `127.0.0.1:1080` + proxy Store).
3. **Тест связи** — внешний IP = выход fr74, не оператора.

## 3. YouT

1. **jap-ridetube-d**, затем **YouT**.
2. **Proxy Store** — вкл (по умолчанию в нашем контуре).
3. Health check, вход по коду TV.

## 4. Если YouTube не открывается

| Симптом | Проверка |
|---------|-----------|
| Нет сети | mgu-uplink, тест в Krikun: сеть |
| Health «proxy» | обход запущен? `proxy = socks5://127.0.0.1:1080` |
| jap-node22 | установлен из **main**, не «no source has» |

## Обновление RideTube из upstream

```bash
python3 scripts/fetch-ridetube.py
python3 scripts/apply-ridetube-patches.py
python3 scripts/verify-ridetube.py
git push origin main
```

На ГУ: обновить каталог источника **main** и переустановить пакеты при смене версий.