# Bonus Task: 5000+ Data Science & IT Job Postings

Проект для допзадания на 5 баллов:
- скрейпинг вакансий DS/IT;
- очистка и препроцессинг;
- интерактивный дашборд;
- готовность к публикации в GitHub и деплою.

## Источник данных
Используется открытый `The Muse Public Jobs API`:
- https://www.themuse.com/developers/api/v2

Сбор выполняется по IT/DS категориям:
- `Software Engineering`
- `Data and Analytics`
- `Science and Engineering`
- `Computer and IT`
- `Product Management`

## Структура
- `scripts/scrape_themuse_jobs.py` — сбор вакансий в `JSONL`
- `scripts/preprocess_jobs.py` — очистка, dedup, классификация `Data Science` / `IT`
- `dashboard/app.py` — Streamlit-дашборд
- `data/raw/` — сырые данные
- `data/processed/` — очищенные данные

## Быстрый запуск
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_pipeline.sh
streamlit run dashboard/app.py
```

После запуска pipeline в `data/processed/summary.json` будет отчёт с количеством строк.
Скрипт `preprocess_jobs.py` завершится ошибкой, если после очистки < 5000 строк (`--min-rows 5000`).

## Что делает очистка
- удаляет HTML и нормализует текст;
- удаляет дубли (`source+id`, потом `title+company+location`);
- оставляет только релевантные DS/IT вакансии по ключевым словам;
- строит признаки:
  - `track` (`Data Science` / `IT`)
  - `country`
  - `is_remote_or_hybrid`
  - `published_month`

## Дашборд
Дашборд содержит:
- KPI: число вакансий, компаний, стран, доля remote/hybrid;
- распределение по `track`;
- топ стран;
- месячный тренд;
- топ компаний;
- табличный просмотр вакансий с фильтрами.

## Публикация на GitHub
```bash
git init
git add .
git commit -m "bonus task: scrape, clean and dashboard for 5000+ DS/IT jobs"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## Деплой визуализации
### Вариант 1: Streamlit Community Cloud
1. Залить проект в GitHub.
2. Войти в https://share.streamlit.io
3. Выбрать репозиторий, ветку `main`, файл `dashboard/app.py`.
4. Нажать Deploy и получить публичную ссылку.

### Вариант 2: Render (Web Service)
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`

## Примечание по дедлайну
Дедлайн в условии: **11 мая**. В проекте оставлен полный воспроизводимый pipeline, чтобы можно было быстро пересобрать данные перед публикацией.
