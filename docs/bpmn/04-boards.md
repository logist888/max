# Процессы бордов (P-BOARD-*) и консолидация Owner

> Источник: MMS Том II гл. 4–10. Каждый борд — частный случай `P-MGMT-01`: его alert-маршруты
> вызывают общий цикл и переиспользуемые sub-processes. Снимок 27.06.2026.

Общий шаблон процесса борда: `timer/event start → KPI Engine (P-DATA) → Alert → SP-DRILL →
SP-ROOTCAUSE → SP-PB-00X → Decision (человек) → Execution → SP-VERIFY → Knowledge`. Ниже —
специфика триггеров, владельцев и alert→playbook на каждом борде.

## P-OWNER-01 — Консолидация и решения собственника (L1→L0)

```mermaid
flowchart TD
  T0(["timer 08:00"]):::ev --> Brief["AI Morning Brief: что изменилось / риски / ≤5 решений [AI]"]
  Brief --> Read["Owner Dashboard: стратегические KPI [user]"] --> G{"Critical Alerts?"}:::gw
  G -- да --> Dq["Decision Queue: ≤5 решений [user]"] --> Del["Делегировать: KPI/срок/владелец [user]"] --> Ctrl["Контроль результата (не процесса)"]
  G -- нет --> Cal["Календарь / исполнение"]
  Del --> M[["P-MGMT-01"]]:::sp
  classDef ev fill:#eef,stroke:#88a; classDef gw fill:#fdf6e3,stroke:#b58900; classDef sp fill:#eafaf0,stroke:#197a4b;
```
`P-OWNER-01` · владелец Owner · ежедневно (08:00) · **правило пяти решений**; консолидирует оба
потока (единственная точка пересечения потока-1 и потока-2).

## P-BOARD-FIN — Финансовое управление
Владелец CFO · ежедневно (Cash/Runway) + ежемесячно (P&L). Alert-маршруты:
| Событие | Шлюз | Playbook |
|---|---|---|
| Runway < 6 мес | Critical | `SP-PB-002` |
| Burn > бюджета | Critical | `SP-PB-002` |
| Contribution < 0 | Critical | `SP-PB-001` |
| Просрочка ДЗ / ликвидность | Warning | наблюдение → CFO |
```mermaid
flowchart LR
  S(["event: фин. KPI"]):::ev --> A["Alert (Runway/Burn/Contribution)"] --> D[["SP-DRILL: P&L↓Contribution↓Variable Costs"]]:::sp --> PB[["SP-PB-002"]]:::sp --> Dec{"Решение CFO/Owner"}:::gw --> Ex["Сценарий: −15% costs"] --> V[["SP-VERIFY"]]:::sp
  classDef ev fill:#eef,stroke:#88a; classDef gw fill:#fdf6e3,stroke:#b58900; classDef sp fill:#eafaf0,stroke:#197a4b;
```

## P-BOARD-MKT — Управление маркетингом
Владелец CMO · еженедельно. Alerts: CAC +20% → `SP-PB-003`; ROMI < 0; DRR > цель; CTR ↓.
```mermaid
flowchart LR
  S(["event: CAC/ROMI/DRR"]):::ev --> A["Alert"] --> D[["SP-DRILL: CAC↓Channel↓Campaign↓Audience↓Creative"]]:::sp --> PB[["SP-PB-003"]]:::sp --> Dec{"Решение CMO"}:::gw
  Dec -- отключить кампанию --> Ex1["Stop Meta-7 [service]"]
  Dec -- перелить бюджет --> Ex2["Reallocate → Referral/SEO [user]"]
  Ex1 --> V[["SP-VERIFY"]]:::sp
  Ex2 --> V
  classDef ev fill:#eef,stroke:#88a; classDef gw fill:#fdf6e3,stroke:#b58900; classDef sp fill:#eafaf0,stroke:#197a4b;
```

## P-BOARD-SALES — Управление продажами
Владелец Commercial Director · еженедельно. Alerts: Pipeline ↓; Win Rate ↓; сделка без активности;
риск потери крупного клиента. Drill: `Revenue↓Manager↓Deal↓Proposal↓Payment`. Воронка
`Qualified Lead→Discovery→Proposal→Negotiation→Agreement→Payment`; Sales Velocity > норматива →
escalation. Playbook: `SP-PB-001` (Revenue).

## P-BOARD-OPS — Управление операциями и Capacity (содержит узкое место)
Владелец COO · ежедневно. Alerts: Capacity > 95% → `SP-PB-004`; Queue > уровня; SLA нарушение;
недостаток экспертов; перегрузка AI → `SP-PB-005`.
```mermaid
flowchart TD
  S(["event: Capacity/Queue/SLA"]):::ev --> A["Alert"] --> G{"Utilization?"}:::gw
  G -- ">95% (критич.)" --> PB4[["SP-PB-004"]]:::sp --> Hire["Hiring Forecast: +N экспертов [rule]"]
  G -- "Queue > SLA" --> Bottle["★ Узкое место: очередь проверки отчётов"]:::bn
  Bottle --> Obs["Наблюдаемость: WIP, p90 ожидания, доля правок [service]"]
  Hire --> Dec{"Решение COO"}:::gw --> V[["SP-VERIFY"]]:::sp
  Obs --> Dec
  classDef ev fill:#eef,stroke:#88a; classDef gw fill:#fdf6e3,stroke:#b58900; classDef sp fill:#eafaf0,stroke:#197a4b; classDef bn fill:#fbeae8,stroke:#b23a36;
```

## P-BOARD-EXP — Управление экспертной сетью
Владелец Head of Expert Network · еженедельно. Alerts: Utilization > 95%; Rating ↓; рост жалоб;
падение NPS; высокая вероятность увольнения. Drill: `Contribution↓Expert↓Client↓Consultation↓Payment`.
Матрица эффективности (качество × Revenue) — business-rule классификация в Stars/Improvement/Risk.

## P-BOARD-PROD — Управление продуктами
Владелец Chief Product Officer · ежеквартально (Product Review). Решения: масштабировать /
оптимизировать / репозиционировать / изменить цену / объединить / закрыть. Матрица продуктов
(Contribution × Growth).
> **GAP:** разделы Product Alerts / Performance / критерии приёмки в источнике отсутствуют
> (Том II §10 оборван на §10.11) — соответствующие alert-маршруты и SLA не достроены, помечены
> аннотацией GAP; процесс ограничен Product Review и матрицей.
