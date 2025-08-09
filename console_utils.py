"""
Beautiful console output utilities for US Visa Rescheduler
Provides colored, formatted console messages for better user experience
"""

from datetime import datetime

from colorama import Back, Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class Console:
    """Beautiful console output utilities"""

    @staticmethod
    def _get_timestamp():
        """Get formatted timestamp"""
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def success(message: str, prefix: str = "SUCCESS"):
        """Print success message in green"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.GREEN}🎉 [{timestamp}] {prefix}: {message}{Style.RESET_ALL}")

    @staticmethod
    def error(message: str, prefix: str = "ERROR"):
        """Print error message in red"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.RED}❌ [{timestamp}] {prefix}: {message}{Style.RESET_ALL}")

    @staticmethod
    def warning(message: str, prefix: str = "WARNING"):
        """Print warning message in yellow"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.YELLOW}⚠️  [{timestamp}] {prefix}: {message}{Style.RESET_ALL}")

    @staticmethod
    def info(message: str, prefix: str = "INFO"):
        """Print info message in blue"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.BLUE}ℹ️  [{timestamp}] {prefix}: {message}{Style.RESET_ALL}")

    @staticmethod
    def searching(message: str):
        """Print searching message in cyan"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.CYAN}🔍 [{timestamp}] SEARCHING: {message}{Style.RESET_ALL}")

    @staticmethod
    def found_slot(date_str: str):
        """Print found slot message with celebration"""
        timestamp = Console._get_timestamp()
        print(f"\n{Back.GREEN}{Fore.BLACK}{'=' * 60}{Style.RESET_ALL}")
        print(
            f"{Back.GREEN}{Fore.BLACK}🎯 [{timestamp}] APPOINTMENT SLOT FOUND ON {date_str}!!! 🎯{Style.RESET_ALL}"
        )
        print(f"{Back.GREEN}{Fore.BLACK}{'=' * 60}{Style.RESET_ALL}\n")

    @staticmethod
    def session_start(session_number: int):
        """Print session start message"""
        timestamp = Console._get_timestamp()
        print(f"\n{Fore.MAGENTA}{'─' * 50}{Style.RESET_ALL}")
        print(
            f"{Fore.MAGENTA}🚀 [{timestamp}] Starting Session #{session_number}{Style.RESET_ALL}"
        )
        print(f"{Fore.MAGENTA}{'─' * 50}{Style.RESET_ALL}")

    @staticmethod
    def session_retry(retry_count: int):
        """Print session retry message"""
        timestamp = Console._get_timestamp()
        print(
            f"{Fore.CYAN}🔄 [{timestamp}] Session retry #{retry_count}{Style.RESET_ALL}"
        )

    @staticmethod
    def date_check(date_str: str, acceptable: bool = False):
        """Print date availability check"""
        timestamp = Console._get_timestamp()
        if acceptable:
            print(
                f"{Fore.GREEN}📅 [{timestamp}] Earliest available date: {date_str} ✅{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.YELLOW}📅 [{timestamp}] Earliest available date: {date_str} (too late){Style.RESET_ALL}"
            )

    @staticmethod
    def login_status(success: bool):
        """Print login status"""
        timestamp = Console._get_timestamp()
        if success:
            print(
                f"{Fore.GREEN}🔐 [{timestamp}] Successfully logged in{Style.RESET_ALL}"
            )
        else:
            print(f"{Fore.RED}🔐 [{timestamp}] Login failed{Style.RESET_ALL}")

    @staticmethod
    def reschedule_status(success: bool):
        """Print reschedule status with celebration or failure"""
        timestamp = Console._get_timestamp()
        if success:
            print(f"\n{Back.GREEN}{Fore.BLACK}{'🎊' * 20}{Style.RESET_ALL}")
            print(
                f"{Back.GREEN}{Fore.BLACK}🎊 [{timestamp}] SUCCESSFULLY RESCHEDULED!!! 🎊{Style.RESET_ALL}"
            )
            print(f"{Back.GREEN}{Fore.BLACK}{'🎊' * 20}{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.RED}❌ [{timestamp}] Rescheduling failed{Style.RESET_ALL}")

    @staticmethod
    def progress_bar(current: int, total: int, description: str = "Progress"):
        """Print a simple progress indicator"""
        percentage = (current / total) * 100
        filled_length = int(50 * current // total)
        bar = "█" * filled_length + "░" * (50 - filled_length)
        print(
            f"\r{Fore.BLUE}{description}: |{bar}| {percentage:.1f}% ({current}/{total}){Style.RESET_ALL}",
            end="",
        )
        if current == total:
            print()  # New line when complete

    @staticmethod
    def separator(title: str = "", char: str = "═"):
        """Print a separator line with optional title"""
        if title:
            separator_line = f" {title} ".center(60, char)
            print(f"{Fore.MAGENTA}{separator_line}{Style.RESET_ALL}")
        else:
            print(f"{Fore.MAGENTA}{char * 60}{Style.RESET_ALL}")

    @staticmethod
    def email_sent(recipient: str):
        """Print email notification sent message"""
        timestamp = Console._get_timestamp()
        print(
            f"{Fore.GREEN}📧 [{timestamp}] Email notification sent to {recipient}{Style.RESET_ALL}"
        )

    @staticmethod
    def max_retries_reached():
        """Print max retries reached message"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.RED}⏰ [{timestamp}] Maximum retries reached{Style.RESET_ALL}")

    @staticmethod
    def max_time_reached():
        """Print max time reached message"""
        timestamp = Console._get_timestamp()
        print(f"{Fore.RED}⏰ [{timestamp}] Maximum time limit reached{Style.RESET_ALL}")

    @staticmethod
    def waiting(seconds: int, reason: str = ""):
        """Print waiting message"""
        timestamp = Console._get_timestamp()
        reason_text = f" ({reason})" if reason else ""
        print(
            f"{Fore.YELLOW}⏳ [{timestamp}] Waiting {seconds} seconds{reason_text}...{Style.RESET_ALL}"
        )

    @staticmethod
    def debug(message: str):
        """Print debug message in dim style"""
        timestamp = Console._get_timestamp()
        print(f"{Style.DIM}🐛 [{timestamp}] DEBUG: {message}{Style.RESET_ALL}")
