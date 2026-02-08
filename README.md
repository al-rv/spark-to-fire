# ✨ Spark to Fire 🔥

A simple desktop Kanban-style board for tracking learning ideas—from spark to completed (fire). Built with Python and CustomTkinter.

## Features

- **Four columns:** Spark (envisioned) → In Progress ⏳ → Discarded / Fire (completed)
- Add learning items with a title and type (tutorial, course, book, idea, etc.)
- Move items between columns; mark completed or discard
- Data stored locally in `data.json` (created on first run)
- Optional emoji images via Twemoji (falls back to text if not available)

## Requirements

- Python 3.11+
- See `requirements.txt` for dependencies

## Setup & run

```bash
pip install -r requirements.txt
python app.py
```

## Project layout

| File           | Purpose                    |
|----------------|----------------------------|
| `app.py`       | Main UI (CustomTkinter)    |
| `logic.py`     | State transitions, decay   |
| `storage.py`   | Load/save `data.json`     |
| `emoji_assets.py` | Optional emoji images  |
| `data.json`    | Local data (auto-created) |

## License

Use and modify as you like.
