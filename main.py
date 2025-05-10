import os
import ssl
import json
import requests
import logging
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import certifi
from dotenv import load_dotenv
from data_recorder import DataRecorder
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Initialize data recorder
data_recorder = DataRecorder()

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()  # This will output to console
    ]
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

def search_youtube(query):
    """Search YouTube for videos"""
    try:
        # Sanitize query
        sanitized_query = re.sub(r'[^\w\s-]', '', query)
        if not sanitized_query:
            raise ValueError("Invalid search query")

        # Configure yt-dlp options for search
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'max_downloads': 5
        }

        results = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for videos
            search_results = ydl.extract_info(f"ytsearch5:{sanitized_query}", download=False)
            
            if not search_results or 'entries' not in search_results:
                logger.error(f"No results found for query: {sanitized_query}")
                return []

            # Process each result
            for entry in search_results['entries']:
                if entry:
                    video_id = entry.get('id', '')
                    # Skip results with invalid video IDs
                    if not video_id or len(video_id) != 11:  # YouTube video IDs are exactly 11 characters
                        logger.warning(f"Skipping result with invalid video ID: {video_id}")
                        continue
                        
                    # Safely get duration and view count
                    duration = entry.get('duration', 0)
                    if isinstance(duration, (int, float)):
                        minutes = int(duration // 60)
                        seconds = int(duration % 60)
                        duration_str = f"{minutes}:{seconds:02d}"
                    else:
                        duration_str = "Unknown"

                    view_count = entry.get('view_count', 0)
                    if isinstance(view_count, (int, float)):
                        view_str = f"{int(view_count):,}"
                    else:
                        view_str = "Unknown"

                    results.append({
                        'id': entry.get('id', ''),
                        'title': entry.get('title', 'Unknown Title'),
                        'artist': entry.get('uploader', 'Unknown Artist'),
                        'duration_str': duration_str,
                        'view_str': view_str
                    })

        return results

    except Exception as e:
        logger.error(f"Error in search_youtube: {str(e)}")
        raise

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /search command"""
    if not context.args:
        await update.message.reply_text(
            "Please provide a song name to search.\n"
            "Example: /search shape of you"
        )
        return

    query = ' '.join(context.args)
    user_id = update.effective_user.id
    
    try:
        # Log the search attempt
        logger.info(f"User {user_id} searching for: {query}")
        
        # Perform the search
        results = search_youtube(query)
        
        if not results:
            error_msg = f"No results found for query: {query}"
            logger.warning(error_msg)
            data_recorder.log_error(
                user_id,
                "search_no_results",
                error_msg,
                {"query": query}
            )
            await update.message.reply_text(
                "❌ No results found. Please try:\n"
                "• Different search terms\n"
                "• More specific song title\n"
                "• Including artist name"
            )
            return

        # Create keyboard with results
        keyboard = []
        for result in results:
            # Format view count to be more concise (e.g., 1.2M, 100K)
            view_count = result['view_str']
            if view_count != "Unknown":
                try:
                    views = int(view_count.replace(',', ''))
                    if views >= 1_000_000:
                        view_str = f"{views/1_000_000:.1f}M"
                    elif views >= 1_000:
                        view_str = f"{views/1_000:.1f}K"
                    else:
                        view_str = str(views)
                except ValueError:
                    view_str = view_count
            else:
                view_str = "0"

            # Create button text with more characters and better formatting
            button_text = (
                f"🎵 {result['title'][:50]}\n"  # Show up to 50 characters of title
                f"👤 {result['artist'][:30]}\n"  # Show up to 30 characters of artist
                f"⏱ {result['duration_str']} | {view_str} views"  # Always show duration, concise views
            )
            
            # Add ellipsis if title or artist is truncated
            if len(result['title']) > 50:
                button_text = button_text.replace(result['title'][:50], result['title'][:47] + "...")
            if len(result['artist']) > 30:
                button_text = button_text.replace(result['artist'][:30], result['artist'][:27] + "...")
            
            # Use a shorter prefix and encode the video ID to handle special characters
            video_id = result['id']
            callback_data = f"dl_{video_id}"  # Keep the full video ID
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Select a song to download:",
            reply_markup=reply_markup
        )
        
        # Log successful search
        data_recorder.log_search(
            user_id,
            query,
            len(results)
        )
        
    except ValueError as ve:
        error_msg = str(ve)
        logger.warning(f"Invalid search query from user {user_id}: {error_msg}")
        data_recorder.log_error(
            user_id,
            "invalid_query",
            error_msg,
            {"query": query}
        )
        await update.message.reply_text(
            "❌ Invalid search query. Please use only letters, numbers, and spaces."
        )
        
    except Exception as e:
        error_msg = f"Error searching for '{query}': {str(e)}"
        logger.error(error_msg)
        data_recorder.log_error(
            user_id,
            "search_error",
            error_msg,
            {"query": query}
        )
        await update.message.reply_text(
            "❌ An error occurred while searching. Please try again in a few moments."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("dl_"):
        # Get the full video ID after the prefix
        video_id = query.data[3:]  # Get everything after "dl_"
        
        # Validate video ID
        if not video_id or len(video_id) != 11:  # YouTube video IDs are exactly 11 characters
            error_msg = f"Invalid video ID: {video_id}"
            logger.error(error_msg)
            data_recorder.log_error(
                update.effective_user.id,
                "invalid_video_id",
                error_msg,
                {"video_id": video_id}
            )
            await query.edit_message_text("❌ Invalid video ID. Please try searching again.")
            return
            
        try:
            # Delete the selection message
            await query.message.delete()
            
            # Send temporary downloading message
            downloading_msg = await query.message.reply_text("⏳ Downloading...")
            
            # Get video info
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                title = info.get('title', 'Unknown Title')
                artist = info.get('uploader', 'Unknown Artist')
            
            # Download the audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': f'downloads/{video_id}.%(ext)s',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            # Send the audio file
            audio_path = f'downloads/{video_id}.mp3'
            with open(audio_path, 'rb') as audio:
                await query.message.reply_audio(
                    audio,
                    title=title,
                    performer=artist,
                    caption=f"🎵 {title}\n👤 {artist}"
                )
            
            # Clean up
            os.remove(audio_path)
            
            # Delete the downloading message
            await downloading_msg.delete()
            
            # Log the download
            data_recorder.log_download(
                update.effective_user.id,
                video_id,
                title,
                artist
            )
            
        except Exception as e:
            error_msg = f"Error downloading video {video_id}: {str(e)}"
            logger.error(error_msg)
            data_recorder.log_error(
                update.effective_user.id,
                "download_error",
                error_msg,
                {"video_id": video_id}
            )
            # Delete the downloading message if it exists
            try:
                await downloading_msg.delete()
            except:
                pass
            await query.message.reply_text("❌ An error occurred while downloading. Please try again later.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stats command to show bot statistics"""
    stats = data_recorder.get_stats()
    if stats:
        message = (
            "📊 Bot Statistics:\n\n"
            f"Total Searches: {stats['total_searches']}\n"
            f"Total Downloads: {stats['total_downloads']}\n"
            f"Total Errors: {stats['total_errors']}\n\n"
            "Last Updated: {}\n".format(
                datetime.fromisoformat(stats['last_updated']).strftime('%Y-%m-%d %H:%M:%S')
            )
        )
        
        # Add top 5 popular searches
        if stats['popular_searches']:
            message += "\n🔍 Top 5 Popular Searches:\n"
            sorted_searches = sorted(
                stats['popular_searches'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for search, count in sorted_searches:
                message += f"- {search}: {count} times\n"
        
        # Add top 5 popular artists
        if stats['popular_artists']:
            message += "\n👤 Top 5 Popular Artists:\n"
            sorted_artists = sorted(
                stats['popular_artists'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for artist, count in sorted_artists:
                message += f"- {artist}: {count} times\n"
        
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("❌ Unable to retrieve statistics at this time.")

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Create downloads directory if it doesn't exist
    os.makedirs('downloads', exist_ok=True)
    
    # Start the bot
    print("🎵 Music Search Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()