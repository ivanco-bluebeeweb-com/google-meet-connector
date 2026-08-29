# Google Meet Connector — UI Component Plan

Источник: `UI_COMPONENT_VOCABULARY.md` (строго примитивы `imperal_sdk.ui`) +
паттерн Google Drive Connector (тот же `ext.oauth("google", ...)`, тот же
`ctx.oauth_authorize_url`). Правила применены: без `Card` в сайдбаре, ровно
одна кнопка "App settings" внизу сайдбара, лейбл + контекстный placeholder на
каждом инпуте (здесь инпутов в форме подключения нет — OAuth flow работает
через кнопку "Continue with Google"), форма/контент растянуты на всю ширину
сайдбара, никаких инструкций, дублирующих модалку кнопки.

## §0. Разница с реализацией сейчас
Этот план пишется ДО `panels.py`, как требует стандарт. `panels.py` будет
написан строго по нему ниже.

## 1. Left sidebar (`slot="left"`)
- Не подключено:
  - `ui.Stack(direction="v", gap=3, align="stretch")`
    - `ui.Empty(message="No Google account connected yet.")`
    - `ui.Button("Continue with Google", icon="ExternalLink", full_width=True, on_click=ui.Open(<oauth_authorize_url>))`
- Подключено (1+ аккаунт):
  - Список аккаунтов `ui.ListItem` (email, статус "Connected"/"Needs reconnecting")
  - Если проблема с токеном — `ui.Alert(type="warning")` + кнопка "Continue with Google" повторно
  - `ui.Button("Connect another account", variant="ghost", size="sm", icon="Plus", on_click=ui.Open(<oauth_authorize_url>))`
- `ui.Divider()`
- Ровно одна `ui.Button("App settings", variant="secondary", size="sm", full_width=True, icon="Settings", on_click=ui.Call("__panel__meet_settings"))`

## 2. Center panel (`slot="center"`)
- Обзор Meet-пространств текущего аккаунта: `ui.ListItem` на каждый
  space/conference record, клик открывает детали (участники, записи,
  транскрипты) через `ui.Call` с параметрами.
- Кнопка "Create meeting space" → `ui.Form(action="create_space", ...)`.

## 3. App settings modal (`slot="center", center_overlay=True`)
- Список подключённых аккаунтов с кнопкой "Disconnect" на каждом (единственное
  место, где есть disconnect — не дублируется в сайдбаре).
- Инструкция "How do I connect?" здесь, не в сайдбаре (избегаем дублирования).
