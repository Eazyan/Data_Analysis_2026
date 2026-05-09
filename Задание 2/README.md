# Задание 2. API-пайплайн: данные -> LLM -> JSON

Студент: Лёгкий Антон Дмитриевич  
Группа: Б9123-01.03.02ии

## Задача

Скрипт читает CSV-файл с отзывами пользователей, отправляет отзывы в LLM через API и получает структурированный JSON:

- тональность: `positive`, `negative`, `neutral`;
- тема отзыва;
- уверенность модели;
- краткое объяснение.

Основной провайдер: OpenRouter. Модель по умолчанию: `qwen/qwen3.6-plus`.

## Структура

- `input/reviews.csv` — входной CSV-файл.
- `src/pipeline.py` — основной скрипт.
- `output/reviews_classified.json` — результат работы скрипта.
- `.env.example` — пример переменных окружения.

## Запуск

```bash
cd "Задание 2"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

В файле `.env` нужно указать ключ OpenRouter:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=qwen/qwen3.6-plus
```

Запуск пайплайна:

```bash
python src/pipeline.py
```

После запуска результат будет сохранен в `output/reviews_classified.json`.

## Ollama

Скрипт также можно запустить через локальный OpenAI-compatible endpoint Ollama:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5-coder:7b
```

## Пример входных данных

```csv
id,review
1,"Приложение быстро запускается, интерфейс понятный, но не хватает экспорта в Excel."
```

## Пример выходных данных

```json
{
  "items": [
    {
      "id": "1",
      "sentiment": "positive",
      "topic": "интерфейс и экспорт",
      "confidence": 0.78,
      "reason": "Отзыв в целом положительный, но содержит пожелание по экспорту."
    }
  ]
}
```
