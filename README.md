# Claude Chat Terminal

A lightweight **terminal interface for Claude.ai**, using Selenium + undetected-chromedriver to automate the Claude web app with your own subscription.

## Features

- Use Claude from the terminal (no API keys required)
- Persistent login saved in `~/.claude_terminal_chrome/`
- Simple commands: `/new`, `/help`, `/debug`, `/exit`

## Install

```bash
pip install undetected-chromedriver selenium
```

## Run

```bash
python claude_chat_terminal.py
```

- A Chrome window opens — log in to Claude.ai if needed.
- Then type messages in the terminal; replies print under **Claude:**.

## Commands

- `/new` – start a new chat
- `/help` – show help
- `/debug` – debug info
- `/exit` – quit

## Notes

- Requires Google Chrome installed.
- If selectors break after UI changes, update `get_all_messages()` and `send_message()`.
- Uses your own Claude.ai subscription; check Anthropic’s ToS.
