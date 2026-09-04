# Переезд MainExperts на Gitea

Сделано после блокировки GitHub-аккаунта: `github.com/logist888/max` отдаёт **403**,
забрать оттуда больше нечего. Здесь — всё, что успело осесть локально, плюс
готовая обвязка под Gitea.

## Шаг 1. Куда именно переезжаем

Gitea бывает трёх видов — выбор влияет только на адрес:

| Вариант | Адрес | Комментарий |
|---|---|---|
| **Codeberg** | codeberg.org | Бесплатный публичный Gitea. Приватные репозитории есть. Ничего поднимать не надо |
| **gitea.com** | gitea.com | Официальный хостинг Gitea |
| **Свой сервер** | ваш домен | Полный контроль. Нужен VPS и docker |

Для приватного репозитория с материалами Потока 1 подойдёт любой — важно лишь
поставить галочку **Private** при создании.

## Шаг 2. Развернуть репозиторий из бандла

Создайте на Gitea **пустой** репозиторий: без README, без .gitignore, без лицензии —
иначе первый push упрётся в конфликт.

```bash
git clone mainexperts-max-full.bundle mainexperts-max
cd mainexperts-max
git fetch origin "+refs/heads/*:refs/heads/*"

git remote set-url origin https://ВАШ-GITEA/ВАШ-АККАУНТ/mainexperts-max.git
git push -u origin --all
git push origin --tags
```

Что уедет: 89 коммитов, ветка `claude/education-seo-platform-p5k4i8` со всей работой,
ветка `claude/sweet-thompson-o8ml5c` (целиком входит в первую), тег
`design-caramel-v1` → коммит `13239c9` (откат к карамельному дизайну).

Проверить после push:

```bash
git rev-list --count --all   # 89
git tag                      # design-caramel-v1
```

## Шаг 3. Переименовать ветку (по желанию)

Имена `claude/...` достались от прежнего процесса. Разумно сделать `main`:

```bash
git branch -m claude/education-seo-platform-p5k4i8 main
git push -u origin main
```
Затем в Settings Gitea назначить `main` веткой по умолчанию. Workflow это учитывает —
он срабатывает и на `main`, и на старое имя.

## Шаг 4. Деплой на прод. Два пути

Прод `vuz-navigator.ru` — статика на FTP-хостинге, от гита не зависит и сейчас жив.

### Путь А. Скрипт с ноутбука — работает сразу

Ничего настраивать не нужно. Требуется node 22+, npm, lftp, curl.

```bash
cp scripts/.env.deploy.example scripts/.env.deploy   # вписать пароль
./scripts/deploy-ftp.sh --discover    # узнать корень сайта на сервере
./scripts/deploy-ftp.sh --dry-run     # пробный прогон, ничего не меняет
./scripts/deploy-ftp.sh --deploy      # реальная заливка
```

`scripts/.env.deploy` в `.gitignore` — пароль в репозиторий не попадёт (проверено).

### Путь Б. Gitea Actions — автодеплой по push

Файл `.gitea/workflows/deploy-vuz-navigator.yml` уже в репозитории.

**Важно: у Gitea нет своих раннеров.** Пока не поднят `act_runner`, workflow не
запустится. Раннер — один docker-контейнер на любой машине с интернетом:

```bash
docker run -d --name gitea-runner --restart always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e GITEA_INSTANCE_URL=https://ВАШ-GITEA \
  -e GITEA_RUNNER_REGISTRATION_TOKEN=<токен из Settings → Actions → Runners> \
  -e GITEA_RUNNER_LABELS=ubuntu-latest \
  gitea/act_runner:latest
```

Затем в Settings → Actions:

| Тип | Имя | Значение |
|---|---|---|
| Secret | `FTP_SERVER` | `31.31.197.39` |
| Secret | `FTP_USERNAME` | `u3591005` |
| Secret | `FTP_PASSWORD` | **новый** пароль |
| Variable | `FTP_REMOTE_DIR` | корень сайта (даст режим discover) |
| Variable | `SITE_URL` | `https://vuz-navigator.ru` |
| Variable | `FTP_DELETE_STALE` | `true` — только после успешного dry-run |

Порядок первого запуска: `discover` → вписать путь → `dry-run` → `deploy`.

Предохранители одинаковы в обоих путях: заливка отменяется, если собралось меньше
9000 страниц, если пуст `index.html`, `404.html` или `sitemap-index.xml`, либо если
canonical не указывает на боевой домен.

## Шаг 5. Три вещи, которые важнее CI

1. **Repository → Private.** На GitHub репозиторий был публичным, и файл
   `vault/30-entities/potok-1-hnw.md` с лесенкой цен Потока 1 (£3K/£5K, 1.5 млн,
   Family Office 10 млн) отдавался по прямой ссылке кому угодно — проверено, код 200.
   ФИО клиентов там нет. Но эти данные считайте раскрытыми: они лежали открыто и
   могли попасть в кэши и форки. Перенос в приватный репозиторий закрывает будущее,
   но не отменяет прошлого.
2. **Сменить пароль FTP** — он приходил открытым текстом в переписку.
3. **Решить судьбу 14 веток**, оставшихся на заблокированном GitHub (список ниже).

## Чего в бандле НЕТ

Локально было 2 ветки из 16 — контейнер клонировал только рабочую и дефолтную.
Остальные 14 недостижимы:

```
agency-landing-page-svzrhy            lk-path-schema-emails-2dqokb
company-process-map-fk08mp            mainexperts-docs-architecture-pm08hn
document-board-system-kgxtd3          mainexperts-metrics-strategy-ax1x58
mainexperts-screening-landing-nbccyl  mainexperts-strategy-7oz3am
mainexperts-system-map-sy1cej         marketing-strategy-report-bdnger
pensive-einstein-j2eoh6               project-board-prompt-o479iy
russian-language-response-xtidtz      three-stage-quality-iteration-m08a9s
```

Судя по названиям: лендинг агентства, схема ЛК с письмами, карта процессов, метрики,
стратегия, лендинг скрининга, система бордов. Вернуть их можно **только** разблокировав
GitHub-аккаунт — других копий нет. Если там есть незаменимое, апелляция в поддержку
GitHub важнее переезда.

## Проверка, что всё приехало

```bash
git log --oneline -3        # 2b19d69, cd9c9ed, 8d52776
git rev-list --count --all  # 89
git tag                     # design-caramel-v1
ls .gitea/workflows/ scripts/deploy-ftp.sh

cd seo-platform/app && npm ci && npm run pipeline && npm run graph
SITE_URL=https://vuz-navigator.ru npm run build   # 10 235 страниц
```
