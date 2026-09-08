# Переезд MainExperts на Bitbucket

Цель: `https://bitbucket.org/agafonov_agency/max`

GitHub-аккаунт заблокирован, `github.com/logist888/max` отдаёт **403** — забрать
оттуда больше нечего. Здесь всё, что успело осесть локально, плюс обвязка деплоя,
переписанная под Bitbucket.

## Почему пушить будете вы, а не я

Два независимых препятствия, оба проверены:

1. **Присланный ключ — публичный.** `ssh-ed25519 AAAAC3...din-server` — это половина
   пары, которую кладут на сервер. Аутентифицировать никого он не может. Пушить
   можно только приватным ключом, а его присылать в переписку нельзя: он даёт
   полный доступ к репозиторию, и однажды попав в чат, остаётся там навсегда.
2. **Порт 22 из моего окружения закрыт** — наружу проходит только HTTPS. Даже с
   приватным ключом SSH-пуш отсюда не состоялся бы.

Поэтому: разворачиваете бандл на `din-server` (там уже лежит нужный приватный ключ)
и пушите оттуда. Ниже готовые команды.

## Шаг 1. Ключ должен быть в Bitbucket

Проверьте, что публичный ключ `din-server` добавлен:
Personal settings → SSH keys (или Repository settings → Access keys — для доступа
только к этому репозиторию).

Проверка связи с din-server:
```bash
ssh -T git@bitbucket.org
# ожидаемо: "authenticated via ssh key" и список доступных репозиториев
```

## Шаг 2. Развернуть бандл

```bash
git clone mainexperts-max-bitbucket.bundle mainexperts-max
cd mainexperts-max
git fetch origin "+refs/heads/*:refs/heads/*"
git remote set-url origin git@bitbucket.org:agafonov_agency/max.git
```

Приедет: 91 коммит, вся работа по сайту, тег `design-caramel-v1` → коммит `13239c9`
(откат к прежнему карамельному дизайну).

## Шаг 3. Разобраться с существующей веткой main

В репозитории уже есть `main` — значит, простой push упрётся в несовпадение историй.
Сначала посмотрите, что там:

```bash
git fetch origin main
git log --oneline origin/main | head
```

**Если там только initial commit / README** (типовой случай для нового репозитория) —
перезаписываем:

```bash
git branch -m claude/education-seo-platform-p5k4i8 main
git push --force-with-lease -u origin main
git push origin --tags
```

**Если в main есть чужая нужная работа** — не перезаписывайте. Заливайте своей веткой
и сливайте через pull request:

```bash
git push -u origin claude/education-seo-platform-p5k4i8
git push origin --tags
```

Проверка после пуша:
```bash
git rev-list --count --all   # 91
git tag                      # design-caramel-v1
```

## Шаг 4. Деплой на прод

Прод `vuz-navigator.ru` — статика на FTP, от гита не зависит и сейчас работает.

### Основной путь: скрипт с din-server (минут не тратит)

```bash
cp scripts/.env.deploy.example scripts/.env.deploy
nano scripts/.env.deploy          # вписать новый пароль FTP

./scripts/deploy-ftp.sh --discover   # узнать корень сайта на сервере
./scripts/deploy-ftp.sh --dry-run    # пробный прогон, ничего не меняет
./scripts/deploy-ftp.sh --deploy     # реальная заливка
```

Нужны `node 22+`, `npm`, `lftp`, `curl`. Файл `.env.deploy` в `.gitignore` —
пароль в репозиторий не попадёт (проверено через `git check-ignore`).

Удобно повесить на cron, если захотите регулярное обновление.

### Запасной путь: Bitbucket Pipelines

Файл `bitbucket-pipelines.yml` в репозитории. Пайплайны **ручные**, автозапуск по
push намеренно выключен — вот почему:

> Бесплатный тариф Bitbucket даёт **50 минут сборки в месяц**. Один полный деплой —
> сборка ~2 минуты плюс заливка 10 235 файлов по FTP, это 15–30 минут. То есть
> бесплатного лимита хватит на один-два деплоя. Скрипт с din-server минут не тратит
> вообще, поэтому он и основной.

Настройка: Repository settings → Repository variables

| Переменная | Значение | Secured |
|---|---|---|
| `FTP_SERVER` | `31.31.197.39` | нет |
| `FTP_USERNAME` | `u3591005` | нет |
| `FTP_PASSWORD` | **новый** пароль | **да** |
| `FTP_REMOTE_DIR` | корень сайта (даст `discover-ftp`) | нет |
| `SITE_URL` | `https://vuz-navigator.ru` | нет |
| `FTP_DELETE_STALE` | `false` | нет |

Порядок: `discover-ftp` → вписать путь → `dry-run` → `deploy`.

Предохранители одинаковы в обоих путях: заливка отменяется, если собралось меньше
9000 страниц, если пуст `index.html`, `404.html` или `sitemap-index.xml`, либо если
canonical не указывает на боевой домен. Удаление файлов на сервере выключено
по умолчанию.

## Шаг 5. Что сделать помимо переезда

1. **Сменить пароль FTP.** Он приходил открытым текстом в переписку.
2. **Репозиторий держать приватным.** Проверено: сейчас он закрыт, анониму отдаёт 404 —
   это правильно. На GitHub он был публичным, и `vault/30-entities/potok-1-hnw.md`
   с лесенкой цен Потока 1 (£3K/£5K, 1.5 млн, Family Office 10 млн) отдавался по
   прямой ссылке кому угодно. ФИО клиентов там нет. Но эти данные считайте
   раскрытыми: переезд закрывает будущее, прошлое он не отменяет.
3. **Решить судьбу 14 веток**, оставшихся на заблокированном GitHub.

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
git log --oneline -3        # 1d71c71 и раньше
git rev-list --count --all  # 91
git tag                     # design-caramel-v1
ls bitbucket-pipelines.yml scripts/deploy-ftp.sh

cd seo-platform/app && npm ci && npm run pipeline && npm run graph
SITE_URL=https://vuz-navigator.ru npm run build   # 10 235 страниц
```
