# Music Search Bot

A powerful Telegram bot that helps you search and download music from YouTube with advanced features and detailed statistics.

## 🌟 Features

- 🔍 Smart YouTube music search
- 🎵 High-quality audio downloads
- 📊 Detailed search results with:
  - Song duration
  - View count
  - Artist information
- 📈 Comprehensive statistics tracking
- 🛡️ Robust error handling
- 📝 Detailed logging system

## 🚀 Setup

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

## 📱 Usage

1. Start a chat with your bot on Telegram
2. Use the following commands:

### Commands

- `/start` - Start the bot and see welcome message
- `/help` - Show detailed help message
- `/search <song name>` - Search for a song
- `/stats` - View bot statistics

### Search Examples

```
/search shape of you
/search blinding lights the weeknd
/search sunflower post malone
```

### Search Results

Each search result shows:
- 🎵 Song title
- 👤 Artist name
- ⏱ Duration
- 👁 View count

## 📊 Statistics

The bot tracks various statistics including:
- Total searches
- Total downloads
- Popular searches
- Popular artists
- Error rates

View statistics using the `/stats` command.

## 📁 Data Storage

The bot stores data in the following structure:
```
data/
├── search_log.json    # Search history
├── download_log.json  # Download history
├── error_log.json     # Error tracking
├── stats.json        # Statistics
└── bot.log          # Detailed logs
```

## 🔧 Error Handling

The bot includes comprehensive error handling for:
- Invalid search queries
- No results found
- Download failures
- Network issues

## 📝 Logging

Detailed logging system that tracks:
- User actions
- Search queries
- Downloads
- Errors
- System events

## 🤝 Contributing

Feel free to submit issues and pull requests. All contributions are welcome!

## 📄 License

MIT License 