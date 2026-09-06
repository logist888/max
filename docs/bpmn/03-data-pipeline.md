# P-DATA-01 — Конвейер данных и KPI

> Источник: MMS Том II гл. 1.4 (слоистая архитектура), гл. 3 (Dashboard Framework); Том I гл. 9
> (KPI Philosophy). Снимок 27.06.2026.

## Паспорт

| Поле | Значение |
|---|---|
| **ID** | `P-DATA-01` · владелец CTO · триггер: business event · частота: онлайн / ≤5 мин (обновление KPI) |
| **Цель** | Превратить событие в проверяемый KPI и подать его в борд и в цикл решений; Single Source of Truth |
| **Входы** | business events (платежи, заявки, AI-запросы, действия на платформе) |
| **Выходы** | рассчитанный KPI, alert (при пороге), запись в Decision Log |
| **Регулирующие воздействия** | данные несовершеннолетних, длительное хранение профиля (Security/retention — **GAP**: раздел Том II не извлечён); единый каталог KPI |
| **Ресурсы** | ETL, KPI Engine, KPI Catalog (data store), AI Copilot |
| **Показатели** | свежесть данных, полнота, число ошибок, своевременность (≤5 мин) |

## Поток (Mermaid)

```mermaid
flowchart TD
  Ev([Business Event]):::ev --> Raw[("Raw Data (store)")]:::ds
  Raw --> Clean["Очистка / валидация [service]"] --> CG{"Compliance:<br/>PII / несовершеннолетние [rule]"}:::gw
  CG -- блок --> RiskEnd([эскалация Risk]):::ev
  CG -- ок --> Obj[("Business Objects (store)")]:::ds
  Obj --> KPI["KPI Engine: расчёт по официальной формуле [service]"]
  KPI --> Cat[("KPI Catalog · Single Source of Truth (store)")]:::ds
  Cat --> G{"Превышен порог? [rule]"}:::gw
  G -- да -->|message| Alert([Alert → борд / P-MGMT-01]):::ev
  G -- нет --> Dash["Подача в Dashboard [service]"]
  Cat --> Dash
  Dash --> AIx["AI Explain / прогноз по запросу [AI]"]
  classDef ev fill:#eef,stroke:#88a; classDef gw fill:#fdf6e3,stroke:#b58900; classDef ds fill:#eef6ff,stroke:#2a6bb0;
```

> Архитектурное правило: ни один слой не обращается к предыдущему, минуя соседний
> (Events → Raw → Business Objects → KPI → Dashboards → AI → Decisions). Это последовательность
> sequence flow без «прыжков».

## Таблица элементов

| Элемент | Тип | Lane | Примечание |
|---|---|---|---|
| Business Event | message start | System | |
| Raw Data / Business Objects / KPI Catalog | data store | System | KPI Catalog = SSOT |
| Очистка / валидация | service task | System | |
| Compliance | exclusive gateway + rule | System | блок при нарушении |
| KPI Engine | service task | System | одна официальная формула на KPI |
| Превышен порог? | exclusive gateway + rule | System | пороги — GAP (чисел нет) |
| Alert | message end / intermediate | System → борд | вход в `P-MGMT-01` |
| AI Explain / прогноз | AI task | AI Copilot | использует только утверждённые формулы |

**GAP:** детальные ETL-протоколы, Data Dictionary (раздел V Том II), Security/retention (раздел
VII) и интеграции (раздел XII) в извлечённом источнике отсутствуют — соответствующие задачи
помечены как требующие спецификации, точные шаги не достроены.
