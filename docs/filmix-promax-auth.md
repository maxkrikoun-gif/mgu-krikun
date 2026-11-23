# FilmixProMax — привязка аккаунта (как в APK / Lampa)

## Схема (device code)

Тот же поток, что **FilmixProMax на Android** и плагин **Lampa `plugins/online/online.js`**:

1. `GET /api/v2/token_request?` + параметры устройства (без `user_dev_token` или пустой).
2. Ответ: `status: "ok"`, `user_code` (показать пользователю), `code` (временный токен для опроса).
3. Пользователь на **https://filmix.gg/consoles** (или актуальное зеркало) вводит **user_code**.
4. **Один раз** при старте демона (и по кнопке «Обновить» в приложении): `GET /api/v2/user_profile?` + `user_dev_token=<code>`.
5. Когда появился **`user_data`** — сохраняем `code` как постоянный `user_dev_token` на ГУ (`/var/opt/jap-filmix-d/state/account.json`).

Фонового опроса нет: после ввода кода на consoles пользователь жмёт **Обновить** (ещё один `user_profile`). Незавершённая сессия (`user_code` + временный `code`) лежит в `state/pending.json`; **повторный `token_request` не делается**, пока пользователь не нажмёт **Выйти** (сброс pending). Срок жизни кода задаёт **сервер Filmix**, в APK/Lampa на клиенте таймер не крутится.

## Параметры устройства (по умолчанию)

Сверены с **Lampac** / мобильным API; **FilmixProMax APK** может отличаться — см. ниже.

| Параметр | Значение по умолчанию |
|----------|------------------------|
| `user_dev_apk` | `2.2.13` (`FILMIX_DEV_APK`) |
| `user_dev_id` | 16 символов, один раз на ГУ (`state/device_id`) |
| `user_dev_name` | `BMW_MGU` |
| `user_dev_os` | `12` |
| `user_dev_vendor` | `BMW` |
| `app_lang` | `ru_RU` |
| API host | `http://filmixapp.cyou` (`FILMIX_API_HOST`) |

## Сеть (Xray)

Отдельной галочки в приложении **нет**. Демон читает `proxy` из `/var/opt/mgu-updater/updater.local.conf` (как Store и RideTube):

- **Обход выкл** (`krikun_seti` → «Остановить обход») — строки `proxy` нет → запросы к API **напрямую**.
- **Обход вкл** — `proxy = socks5://127.0.0.1:1080` → весь Filmix API через **krikun-xray**.

## Где в репо

| Файл | Роль |
|------|------|
| `native/jap-filmix-d/filmix-auth.js` | `token_request` + один `user_profile` при bootstrap |
| `native/jap-filmix-d/filmix-d.js` | ctl.sock, команды `auth`, `sign_out` |
| `apps/filmix_promax/main.js` | экран с кодом + QR на consoles |

Протокол app ↔ daemon (как у YouT):

- `auth` / `auth_status` / `sign_out` / `auth_refresh`
- события: `auth` с `state`: `signed_out` \| `code` \| `signed_in` \| `error`

## Синхронизация с APK FilmixProMax

APK в git **нет** (лицензия/секреты). Чтобы **1:1** как ProMax:

```bash
# APK на Mac, после декомпиляции jadx или apktool:
bash scripts/scan-filmix-apk.sh /path/to/FilmixProMax.apk
```

Скрипт ищет `user_dev_apk=`, `filmixapp`, `token_request` и подсказывает `FILMIX_DEV_APK` / host.

На ГУ в unit-файле демона можно задать:

```ini
Environment=FILMIX_DEV_APK=...
Environment=FILMIX_API_HOST=...
```

## PRO / качество

После входа в `user_data`:

- `is_pro` → до 1080p
- `is_pro_plus` → до 2160p
- иначе гостевой/бесплатный лимит (как в Lampa `filmix.js`)

Каталог и `play` — следующий этап (`search`, `post/{id}`, плейлист озвучек).