import threading
import uvicorn
import json
import yaml
import os
from pystyle import Colors, Colorate, Center
import logging
import sys
from logger import info, warn, fail, success, debug


logging.getLogger("discord.gateway").setLevel(logging.ERROR)
logging.getLogger("discord.client").setLevel(logging.ERROR)
logging.getLogger("discord.http").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)
logging.getLogger("websockets.client").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.ERROR)

# Custom logging configuration for Uvicorn
class CustomUvicornHandler(logging.Handler):
    def emit(self, record):
        log_message = self.format(record)
        
        # Check if this is an access log (HTTP request)
        if record.name == "uvicorn.access" and " - \"" in log_message and "HTTP/" in log_message:
            debug(log_message)  # Use DGB for route endpoint logs
        elif record.levelno >= logging.ERROR:
            fail(log_message)
        elif record.levelno >= logging.WARNING:
            warn(log_message)
        elif record.levelno >= logging.INFO:
            info(log_message)
        else:
            info(log_message)

def configure_uvicorn_logging():
    # Create custom handler
    custom_handler = CustomUvicornHandler()
    formatter = logging.Formatter('%(message)s')
    custom_handler.setFormatter(formatter)
    
    # Configure root logger to avoid duplicate logs
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure uvicorn loggers to use our custom handler
    loggers = [
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("uvicorn.access"),
    ]
    
    for logger in loggers:
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # Add our custom handler
        logger.addHandler(custom_handler)
        # Set level to INFO so we can see important messages
        logger.setLevel(logging.INFO)
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def load_config():
    try:
        with open('config/config.yaml') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Config file not found!")
        return {"extras": {"port": 8080}}  # Default port if config not found

# Import bot functions - we need to import here to avoid circular imports
def start_discord_bot():
    from bot import start_bot
    start_bot()

banner = """
██████╗  ██████╗  ██████╗ ███████╗████████╗    ██████╗  ██████╗ ████████╗
██╔══██╗██╔═══██╗██╔═══██╗██╔════╝╚══██╔══╝    ██╔══██╗██╔═══██╗╚══██╔══╝
██████╔╝██║   ██║██║   ██║███████╗   ██║       ██████╔╝██║   ██║   ██║   
██╔══██╗██║   ██║██║   ██║╚════██║   ██║       ██╔══██╗██║   ██║   ██║   
██████╔╝╚██████╔╝╚██████╔╝███████║   ██║       ██████╔╝╚██████╔╝   ██║   
╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝       ╚═════╝  ╚═════╝    ╚═╝   
        Boost Bot                              - ds @titanlegit 
                                               - gh @titanleg1t                          

"""

# Main function to start everything
def main():
    config = load_config()
    port = config.get("extras", {}).get("port", 8080)
    print(Center.XCenter(Colorate.Vertical(color=Colors.purple_to_blue, text=banner), spaces=15))
    
    # Configure custom uvicorn logging
    configure_uvicorn_logging()
    
    # Start the Discord bot in a separate thread
    bot_thread = threading.Thread(target=start_discord_bot)
    bot_thread.daemon = True  # Make thread exit when main thread exits
    bot_thread.start()
    
    # Import and start FastAPI app
    from api import app
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", log_config=None)

if __name__ == "__main__":
    clear_console()
    main()

# Crafted With <3 By Bhaskar 