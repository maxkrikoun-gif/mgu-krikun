# Первый запуск на ГУ (krikun + RideTube)

Порядок — отдельные пакеты, одна строка proxy.

## 1. Store

- Источник: **`maxkrikoun-gif/mgu-krikun`**, канал **Releases** → релиз `catalog` (см. [catalog-release.md](catalog-release.md)).  
  Режим **ветка main** — только для разработки; для установки YouT/Filmix нужен **catalog**.
- **mgu-uplink** — из того же catalog (интернет с телефона).
- Сначала база: **mgu-deploy**, **mgu-python**, **jap-node22**, **mgu-render**, **idrive7-renderd**, **mgu-inputgate**.

## 2. Xray

1. Установить **krikun-xray** + **Krikun: сеть**.
2. USB: `KRIKUN/xray.json` → импорт в приложении.
3. **Запустить обход** (SOCKS `127.0.0.1:1080` + proxy Store).
4. **Тест связи** — внешний IP должен быть выходом fr74, не оператора.

## 3. YouT (YouTube)

1. Установить **jap-ridetube-d**, затем **jap_ridetube**.
2. В **YouT**: **«Proxy Store»** — **вкл** (в mgu-krikun по умолчанию вкл, если вы не меняли).
3. **Health check** в меню YouT.
4. Вход: код TV на телефоне.
5. **Видео в движении** в mgu-krikun **вкл по умолчанию**, без экрана согласия и без требования стоянки для включения.
6. **Закрыл YouT** — воспроизведение на паузе; **открыл снова** — по умолчанию продолжается с того же ролика.
7. **Закрыть** — в левой колонке YouT, в меню или на панели; в **Krikun: сеть** — кнопка **Закрыть** на каждом экране.

## 4. Если YouTube не открывается

| Симптом | Проверка |
|---------|-----------|
| Нет сети | uplink, тест в Krikun: сеть |
| Health «proxy» | обход запущен? `proxy = socks5://127.0.0.1:1080` в Store |
| IP в тесте «прямой» | Xray не запущен или proxy не включён |

## Обновление RideTube из upstream

```bash
python3 scripts/fetch-ridetube.py
python3 scripts/apply-ridetube-patches.py
python3 scripts/verify-ridetube.py
```