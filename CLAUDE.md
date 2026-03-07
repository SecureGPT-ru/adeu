# CLAUDE.md — Инструкции для AI-агентов

## Обзор проекта

**ADEU** (Automated DOCX Redlining Engine) — движок для редактирования Word-документов с сохранением Track Changes.

Ключевая идея: LLM работает с текстом, ADEU конвертирует изменения в нативный XML (`w:ins`/`w:del`) без разрушения форматирования.

## Быстрый старт

```bash
# Установка зависимостей (требуется uv)
uv sync

# Запуск тестов
uv run pytest

# Запуск конкретного теста
uv run pytest tests/test_edit_results.py -v
```

## Структура кода

```
src/adeu/
├── models.py          # Pydantic-модели: DocumentEdit, EditResult, EditStatus
├── ingest.py          # Извлечение текста из DOCX → Markdown/CriticMarkup
├── redline/
│   ├── mapper.py      # Маппинг текстовых позиций → XML runs
│   ├── engine.py      # RedlineEngine — основной класс применения правок
│   └── comments.py    # Поддержка комментариев Word
├── server.py          # MCP-сервер (для Claude Desktop)
├── cli.py             # CLI команды (adeu extract, adeu apply, etc.)
└── diff.py            # Сравнение документов
```

## Ключевые классы

### RedlineEngine (engine.py)
Основной класс для применения правок:
```python
from adeu import RedlineEngine, DocumentEdit

engine = RedlineEngine(docx_stream, author="AI")
results = engine.apply_edits([
    DocumentEdit(target_text="старый", new_text="новый")
])
# results: List[EditResult] с status, context_with_markup
```

### EditResult (models.py)
Результат применения правки с обратной связью:
- `status`: EditStatus (APPLIED, SKIPPED_NOT_FOUND, SKIPPED_OVERLAP)
- `context_with_markup`: CriticMarkup `{--old--}{++new++}`

## Интеграция с SecureGPT/LibreChat

ADEU используется как внешний сервис через HTTP API:
- Эндпоинт: `POST /apply-edits-v2`
- Клиент: `AdeuClient.applyEditsWithFeedback()` в `packages/artifacts/`

Переменная окружения: `ADEU_SERVICE_URL`

## Тестирование

```bash
# Все тесты
uv run pytest

# С coverage
uv run pytest --cov=adeu

# Конкретный файл
uv run pytest tests/test_redline_engine.py -v
```

Тесты используют фикстуры из `tests/fixtures/`.

## CriticMarkup

ADEU использует CriticMarkup для представления изменений:
- `{--удалённый текст--}` — deletion
- `{++добавленный текст++}` — insertion
- `{>>комментарий<<}` — comment
- `{==выделение==}` — highlight

## Важные инварианты

1. **Не мержить runs со спецконтентом** (`w:br`, `w:tab`, `w:drawing`)
2. **mapper и ingest синхронизированы** — виртуальные символы учитываются
3. **Fuzzy matching** — небольшие отличия в пробелах допустимы
