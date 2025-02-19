import os
import subprocess
import colorama
from datetime import datetime

class Runner:
    def __init__(self, output_dir, debug=False):  # Explicitly set debug default to False
        self.log_file = os.path.join(output_dir, "logs", "stream.log")  # Consistent naming
        os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)  # Include output_dir
        self.debug = debug
        self.types = ["DISCORD BOT", "WEBSERVER", "SECURITY SYSTEM"]  # Removed extra spaces
        colorama.init()
        self.log(f"{'-'*50} STARTED {'-'*50}\n", started=True) #Consistent spacing

    def log(self, msg: str, started: bool = False):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")  # More descriptive name
        if not started:
            msg = f"[{timestamp}] {msg}"
        with open(self.log_file, "a") as logger:  # Open in append mode ("a")
            logger.write(msg)

    def _print(self, service_type: str, msg: str, level: str = None):  # More descriptive names
        color = {  # Use a dictionary for cleaner color mapping
            self.types[0]: colorama.Fore.CYAN,
            self.types[1]: colorama.Fore.YELLOW,
            self.types[2]: colorama.Fore.MAGENTA,
        }.get(service_type) #Handle the case where the service_type is not in the dictionary

        level_color = {  # Map levels to colors
            "error": colorama.Fore.RED,
            "info": colorama.Fore.GREEN,
            "warning": colorama.Fore.YELLOW,
        }.get(level)

        prefix = f"{colorama.Fore.LIGHTBLACK_EX}|{color}{service_type}{colorama.Fore.LIGHTBLACK_EX}|  {colorama.Fore.GREEN}->{colorama.Fore.RESET}  "
        level_str = f"{level_color}{level.upper()}: " if level else "" # Add level string if level exists
        print(f"{prefix}{level_str}{msg}{colorama.Fore.RESET}\n", end='') #Reset color at the end

        log_msg = f"|{service_type}|  ->  {level_str}{msg}" #Include level information in the log
        self.log(log_msg)

    def exec(self, cmd, service_type: str = "bot"):  # Default to bot, type hint
        err_stream = subprocess.STDOUT if service_type == "web" or self.debug else subprocess.PIPE # More descriptive name
        try:
            with subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=err_stream, bufsize=1, universal_newlines=True
            ) as process:
                for line in process.stdout:
                    level = None
                    if any(prefix in line for prefix in ["INFO:", "W0000"]):  # More flexible prefix matching
                        level = "info"
                    elif any(prefix in line for prefix in ["WARNING:", "   WARNING:"]):
                        level = "warning"

                    self._print(self.types[0] if service_type == "bot" else self.types[1] if service_type == "web" else self.types[2], line.strip(), level) #Strip newline characters from the line

                return_code = process.returncode #Get the return code after the loop has finished

            if return_code != 0:
                self._print(self.types[0] if service_type == "bot" else self.types[1] if service_type == "web" else self.types[2], f"{return_code} {cmd}", "error")  # Log the command itself
            return return_code #Return the return code

        except FileNotFoundError: #Handle FileNotFoundError
            self._print(self.types[0] if service_type == "bot" else self.types[1] if service_type == "web" else self.types[2], f"Command not found: {cmd}", "error")
            return 1 #Return an error code
        except Exception as e: # Catch other potential errors
            self._print(self.types[0] if service_type == "bot" else self.types[1] if service_type == "web" else self.types[2], f"An error occurred: {e}", "error")
            return 1 #Return an error code
