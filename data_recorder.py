import json
import os
from datetime import datetime
import logging

class DataRecorder:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.search_log_file = os.path.join(data_dir, "search_log.json")
        self.download_log_file = os.path.join(data_dir, "download_log.json")
        self.error_log_file = os.path.join(data_dir, "error_log.json")
        self.stats_file = os.path.join(data_dir, "stats.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize log files if they don't exist
        self._initialize_log_files()
        
        # Setup logging to both file and console
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            file_handler = logging.FileHandler(os.path.join(data_dir, "bot.log"))
            console_handler = logging.StreamHandler()
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)

    def _initialize_log_files(self):
        """Initialize log files with empty lists if they don't exist"""
        for file_path in [self.search_log_file, self.download_log_file, self.error_log_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
        
        if not os.path.exists(self.stats_file):
            initial_stats = {
                "total_searches": 0,
                "total_downloads": 0,
                "total_errors": 0,
                "popular_searches": {},
                "popular_artists": {},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.stats_file, 'w') as f:
                json.dump(initial_stats, f, indent=4)

    def _append_to_log(self, file_path, data):
        """Append data to a JSON log file"""
        try:
            with open(file_path, 'r') as f:
                log_data = json.load(f)
            
            log_data.append(data)
            
            with open(file_path, 'w') as f:
                json.dump(log_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error appending to log file {file_path}: {str(e)}")

    def _update_stats(self, stat_type, data=None):
        """Update statistics"""
        try:
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
            
            stats[stat_type] += 1
            
            if data:
                if stat_type == "popular_searches":
                    query = data.get("query", "").lower()
                    stats["popular_searches"][query] = stats["popular_searches"].get(query, 0) + 1
                elif stat_type == "popular_artists":
                    artist = data.get("artist", "").lower()
                    stats["popular_artists"][artist] = stats["popular_artists"].get(artist, 0) + 1
            
            stats["last_updated"] = datetime.now().isoformat()
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error updating stats: {str(e)}")

    def log_search(self, user_id, query, results_count):
        """Log a search operation"""
        search_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query": query,
            "results_count": results_count
        }
        self._append_to_log(self.search_log_file, search_data)
        self._update_stats("total_searches", search_data)
        self.logger.info(f"Search logged: {query} by user {user_id}")

    def log_download(self, user_id, video_id, title, artist):
        """Log a download operation"""
        download_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "video_id": video_id,
            "title": title,
            "artist": artist
        }
        self._append_to_log(self.download_log_file, download_data)
        self._update_stats("total_downloads", download_data)
        self.logger.info(f"Download logged: {title} by {artist} for user {user_id}")

    def log_error(self, user_id, error_type, error_message, context=None):
        """Log an error"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "error_type": error_type,
            "error_message": error_message,
            "context": context
        }
        self._append_to_log(self.error_log_file, error_data)
        self._update_stats("total_errors")
        self.logger.error(f"Error logged: {error_type} - {error_message}")

    def get_stats(self):
        """Get current statistics"""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading stats: {str(e)}")
            return None 