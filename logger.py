import colorama
import time

colorama.init()

def log(message, **kwargs):
    timestamp = time.strftime('%H:%M:%S', time.localtime())
    formatted_message = f"{colorama.Fore.WHITE}[{colorama.Fore.LIGHTMAGENTA_EX}{timestamp}{colorama.Fore.WHITE}] {message}"
    
    if kwargs:
        formatted_message += f" {colorama.Fore.LIGHTBLACK_EX}→ {colorama.Fore.WHITE}"
        for key, value in kwargs.items():
            formatted_message += f"{colorama.Fore.LIGHTBLACK_EX}{key}={colorama.Fore.LIGHTCYAN_EX} {value} "
    
    print(formatted_message)

def fail(message, **kwargs):
    """Log an error message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.RED}ERR{colorama.Fore.WHITE}]{colorama.Fore.RED} › {message}"
    log(prefix, **kwargs)

def error(message, **kwargs):
    """Log an error message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.RED}ERR{colorama.Fore.WHITE}]{colorama.Fore.RED} › {message}"
    log(prefix, **kwargs)

def warn(message, **kwargs):
    """Log a warning message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.LIGHTYELLOW_EX}WRN{colorama.Fore.WHITE}]{colorama.Fore.LIGHTYELLOW_EX} › {message}"
    log(prefix, **kwargs)

def success(message, **kwargs):
    """Log a success message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.LIGHTGREEN_EX}SUC{colorama.Fore.WHITE}]{colorama.Fore.LIGHTGREEN_EX} › {message}"
    log(prefix, **kwargs)

def info(message, **kwargs):
    """Log an info message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.BLUE}INF{colorama.Fore.WHITE}]{colorama.Fore.LIGHTGREEN_EX} › {message}"
    log(prefix, **kwargs)

def debug(message, **kwargs):
    """Log a debug message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.CYAN}DGB{colorama.Fore.WHITE}]{colorama.Fore.CYAN} › {message}"
    log(prefix, **kwargs)

def captcha(message, **kwargs):
    """Log a captcha-related message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.LIGHTBLUE_EX}CAP{colorama.Fore.WHITE}]{colorama.Fore.LIGHTBLUE_EX} › {message}"
    log(prefix, **kwargs)

def update(message, **kwargs):
    """Log an update message"""
    prefix = f"{colorama.Fore.WHITE}[{colorama.Fore.LIGHTMAGENTA_EX}UPD{colorama.Fore.WHITE}]{colorama.Fore.LIGHTCYAN_EX} › {message}"
    log(prefix, **kwargs)
