## Bot

- Configure environment in `.env` (see `.env.example`).
- Install deps: `pip install -r requirements.txt`
- Run: `python -m bot.main`

### Notes
- Uses Pydantic Settings for config.
- Relies on Telegram `until_date` for mutes, no local scheduler.