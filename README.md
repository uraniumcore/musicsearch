# Music Search Bot

A Telegram bot that helps you search and download music from YouTube.

## Features

- 🔍 Search for songs on YouTube
- 🎵 Download high-quality audio
- 🚀 Fast and reliable
- 🎧 Easy to use interface

## Setup

1. Clone the repository:
```bash
git clone https://github.com/uraniumcore/musicsearch.git
cd musicsearch
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file and add your Telegram bot token:
```bash
echo "BOT_TOKEN=your_bot_token_here" > .env
```

5. Run the bot:
```bash
python main.py
```


## Usage

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Use `/search <song name>` to search for songs
4. Click on a song to download it

## Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/search <song name>` - Search for a song

## Contributing

Feel free to submit issues and pull requests.

## License

MIT License 