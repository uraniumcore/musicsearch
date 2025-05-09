import os
import ssl
import json
import requests
import logging
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(cafile=certifi.where())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = (
        "🎵 Welcome to Music Search Bot!\n\n"
        "I can help you find and download your favorite songs from YouTube.\n\n"
        "Available commands:\n"
        "🔍 /search - Search for a song\n"
        "❓ /help - Show detailed help\n\n"
        "Example:\n"
        "/search Sunflower Post Malone\n\n"
        "Just send me a song name and I'll find it for you! 🎧"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = (
        "🎵 Music Search Bot Help\n\n"
        "Commands:\n"
        "🔍 /search - Search for a song\n"
        "Example: /search Sunflower Post Malone\n\n"
        "Features:\n"
        "• High-quality audio downloads\n"
        "• Fast and reliable search\n"
        "• Easy to use interface\n\n"
        "Tips:\n"
        "• Be specific in your search\n"
        "• Include artist name for better results\n"
        "• Wait for download to complete"
    )
    await update.message.reply_text(help_text)

def get_video_info(video_id):
    """Get video information using YouTube's oEmbed API"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', 'Unknown Title'),
                'author': data.get('author_name', 'Unknown Artist')
            }
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
    return None

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search command"""
    query = " ".join(context.args)
    
    if not query:
        help_text = (
            "🔍 How to search:\n\n"
            "Use the command followed by the song name:\n"
            "/search <song name>\n\n"
            "Examples:\n"
            "• /search Sunflower Post Malone\n"
            "• /search Shape of You\n"
            "• /search Blinding Lights The Weeknd"
        )
        await update.message.reply_text(help_text)
        return

    try:
        logger.info(f"Searching for: {query}")
        # Direct YouTube search
        search_url = f"https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%253D%253D"
        logger.info(f"Search URL: {search_url}")
        
        response = requests.get(search_url)
        logger.info(f"Search response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Search request failed with status code: {response.status_code}")
            raise ValueError(f"Search request failed with status code: {response.status_code}")
        
        # Extract video IDs from the response
        video_ids = []
        start_index = 0
        while len(video_ids) < 5:
            start_index = response.text.find('"videoId":"', start_index)
            if start_index == -1:
                logger.info("No more video IDs found in response")
                break
            start_index += 11
            end_index = response.text.find('"', start_index)
            video_id = response.text[start_index:end_index]
            if video_id not in video_ids:
                video_ids.append(video_id)
                logger.info(f"Found video ID: {video_id}")
        
        if not video_ids:
            logger.error("No video IDs found in the response")
            raise ValueError("No results found")
            
        # Get video details
        results = []
        for video_id in video_ids:
            try:
                logger.info(f"Getting details for video ID: {video_id}")
                info = get_video_info(video_id)
                if info:
                    results.append({
                        'title': info['title'],
                        'id': video_id
                    })
                    logger.info(f"Successfully got details for: {info['title']}")
            except Exception as e:
                logger.error(f"Error getting details for video {video_id}: {str(e)}")
                continue
        
        if not results:
            logger.error("No valid results found after processing")
            raise ValueError("No results found")
            
        # Create keyboard markup
        keyboard = []
        for result in results:
            keyboard.append([InlineKeyboardButton(result['title'], callback_data=result['id'])])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎵 Select a song:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    # Edit the message to show downloading status
    await query.edit_message_text("⏬ Downloading your song...")
    
    video_id = query.data
    try:
        # Get video info first
        video_info = get_video_info(video_id)
        if not video_info:
            raise ValueError("Could not get video information")
            
        # Create a safe filename
        safe_title = "".join(c for c in video_info['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_author = "".join(c for c in video_info['author'] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_author} - {safe_title}"
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'downloads/{filename}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading: {filename}")
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        
        # Send the audio file
        audio_path = f'downloads/{filename}.mp3'
        if os.path.exists(audio_path):
            await query.message.reply_audio(
                audio=open(audio_path, 'rb'),
                title=video_info['title'],
                performer=video_info['author']
            )
            # Clean up
            os.remove(audio_path)
            # Delete the downloading message
            await query.message.delete()
        else:
            raise FileNotFoundError("Audio file not found after download")
            
    except Exception as e:
        logger.error(f"Error in button callback: {str(e)}")
        await query.edit_message_text(f"❌ Error: {str(e)}")

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Create downloads directory if it doesn't exist
    os.makedirs('downloads', exist_ok=True)
    
    # Start the bot
    print("🎵 Music Search Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()