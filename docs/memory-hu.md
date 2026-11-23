# Память на ГУ (krikun-xray / krikun_seti)

Краткий аудит и правила — **ОЗУ мало**, `tmpfs` в `/run` тоже съедает RAM.

## Риски (были) и меры

| Риск | Мера |
|------|------|
| Повторный «Запустить тест» → цепочка `setTimeout` | Один активный poll, `clearTimeout`, `releaseUiState()` |
| Отмена теста через `waitResponse` (spin) блокирует event loop | `cancelConnectivityTest()` только пишет запрос, без ожидания |
| Параллельные `connectivity-test` в root | Проверка `TEST_PID` + `kill -0` |
| Забытые `requests/*.json`, `responses/*.json` в `/run` | `reap_stale` каждые ~120 циклов (старше 15 мин) |
| Длинный обход USB при импорте | Лимит **50** `.json` в `listJsonOnMount` |
| Списки флешки/файлов в `view` | `clearImportLists()` при уходе с импорта / входе в тест |

## Процессы

- **Xray** — один child в `start.sh`, без накопления зомби (`wait`).
- **request-processor** — один фон на тест, PID-файл чистится после завершения / reap.
- **ping** — временный `/tmp/krikun-ping.$$`, удаляется сразу.

## Приложению (canvas)

- Долгие операции — только **`runConnectivityTestAsync`**, не синхронный `waitResponse` на UI-потоке.
- По закрытию экрана теста вызывать **`onLeaveTest()`** → `releaseUiState()`.
- Не держать в `view` большие объекты: после отображения достаточно строки из `formatTestResult()`.

## Xray

Потребление RAM задаётся бинарником и конфигом — отдельно от этого клиента. На ГУ не поднимать лишние копии служб.

## Проверка на машине (post-check)

```sh
# На ГУ после нагрузочного сценария: импорт → тест ×5 → отмена
ls /run/krikun-xray/requests /run/krikun-xray/responses 2>/dev/null | wc -l
ps aux | egrep 'request-processor|xray' | grep -v grep
```

Ожидание: нет лишних `request-processor` / зависших subshell, в `responses/` пусто или 0–1 свежий файл.