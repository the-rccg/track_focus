import asyncio
import csv
import json
import os
import pickle
import platform
import threading
import tkinter as tk
from collections import OrderedDict
from datetime import datetime, timedelta
from tkinter import messagebox
from typing import Callable, Dict, Iterable, List, Tuple

import fire
from aiogram import Bot


DEBUG = True


# Handle Platforms
OPERATING_SYSTEM = platform.system()
if OPERATING_SYSTEM == "Windows":
    import pygetwindow as gw
elif OPERATING_SYSTEM == "Linux":
    from Xlib import display
elif OPERATING_SYSTEM == "Darwin":
    import Quartz
    from AppKit import NSWorkspace
else:
    print(f"Could not recognize the Operating System!")
    print(f"System detected:  {OPERATING_SYSTEM}")


def get_script_directory():
    return os.path.dirname(os.path.abspath(__file__))


# Initialize Telegram messaging
token_path = f"{get_script_directory()}/telegram.json"
if os.path.isfile(token_path):
    d = json.load(open())
    BOT_TOKEN = d["telegram"]
    CHAT_ID = d["chat_id"]
    del d
else:
    BOT_TOKEN = None
    CHAT_ID = None


class TrackingApp:
    def __init__(self, root, path='window_tracking', add_to_calendar=False):
        self.root = root
        self.path = path
        self.add_to_calendar = add_to_calendar
        self.is_tracking = False
        self.tracking_task = None
        self.loop = asyncio.get_event_loop()
        self.root.title("Tracking App")

        # Make the window always on top
        self.root.attributes('-topmost', True)

        # Set up the button
        self.button = tk.Button(
            root,
            text="Start Tracking",
            command=self.toggle_tracking,
            bg="red",
            fg="white",
            font=("Helvetica", 16, "bold"),
            padx=20,
            pady=10,
        )
        self.button.pack(pady=0)

        # Check if file already exists & print initial summary
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%d")
        filename = os.path.join(f"{os.path.dirname(os.path.abspath(__file__))}/window_tracking", f"{date_str}.csv")
        if os.path.isfile(filename):
            events = csv_to_event_format(filename)
            print(f"Previous statistics:")
            print(format_events(events))


    def toggle_tracking(self):
        if self.is_tracking:
            self.stop_tracking()
        else:
            self.start_tracking()

    def start_tracking(self):
        self.is_tracking = True
        self.button.config(text="Stop Tracking", bg="green")
        self.tracking_task = threading.Thread(target=self.run_tracking_loop)
        self.tracking_task.start()

    def stop_tracking(self):
        self.is_tracking = False
        self.button.config(text="Start Tracking", bg="red")

        # If the loop is running, cancel the tasks and finalize the tracking
        if self.loop.is_running():
            for task in asyncio.all_tasks(self.loop):
                task.cancel()
        if self.tracking_task:
            self.tracking_task.join()

    def run_tracking_loop(self):
        try:
            self.loop.run_until_complete(track_windows(self.path, self.add_to_calendar))
        except asyncio.CancelledError:
            pass

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.is_tracking:
                self.stop_tracking()
            self.root.destroy()


# Window tracking functions


async def track_windows(save_path, save_interval=300, operating_system = OPERATING_SYSTEM):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    tracked_windows = []
    previous_window = None
    start_time = None
    summary = {}
    rotation_interval = timedelta(days=1)  # Rotate files daily

    # Initialize the rotation time
    next_rotation_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + rotation_interval

    async def periodic_save():
        nonlocal next_rotation_time
        while True:
            if tracked_windows:
                next_rotation_time = await save_to_csv(tracked_windows, save_path, rotation_interval)
                tracked_windows.clear()
            await asyncio.sleep(save_interval)

    asyncio.create_task(periodic_save())

    # Main Loop: Getting & saving current focus window
    try:
        while True:
            window_title = await get_active_window[operating_system]()
            if window_title and (previous_window != window_title):
                if previous_window and start_time:
                    end_time = datetime.now()
                    duration = end_time - start_time
                    if previous_window in summary:
                        summary[previous_window] += duration
                    else:
                        summary[previous_window] = duration

                previous_window = window_title
                start_time = datetime.now()

                timestamp = datetime.now()
                time_str = timestamp.strftime("%H:%M:%S")
                tracked_windows.append([time_str, window_title])
                print(f"Time: {time_str} | Window: {window_title}")

            await asyncio.sleep(1)

    # Wrap-up when stopped
    except asyncio.CancelledError:
        # Add Pause entry
        if previous_window and start_time:
            duration = datetime.now() - start_time
            if previous_window in summary:
                summary[previous_window] += duration
            else:
                summary[previous_window] = duration

            # Record the exit time for the last window
            time_str = datetime.now().strftime("%H:%M:%S")
            tracked_windows.append([time_str, "Pause tracking"])
        # Save remaining
        if tracked_windows:
            await save_to_csv(tracked_windows, save_path, rotation_interval)

        # Produce summary
        events = summary_to_event_format(summary)
        message_text = format_events(events)

        if BOT_TOKEN and CHAT_ID:
            await send_telegram_message(message_text)

        print("Tracking stopped and data saved.")

        # Print Summary
        print()
        print("SESSION SUMMARY:")
        print(message_text)


def get_active_window_windows():
    """Get the active window's title on Windows."""
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            return active_window.title
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_active_window_linux():
    """Get the active window's title on Linux using Xlib."""
    d = display.Display()
    root = d.screen().root
    window_id = root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'), Xlib.X.AnyPropertyType).value[0]
    window = d.create_resource_object('window', window_id)
    window_name = window.get_wm_name()
    return window_name


def get_active_window_macos():
    """Get the active window's title on macOS."""
    active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    active_pid = active_app.processIdentifier()
    options = Quartz.kCGWindowListOptionOnScreenOnly
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

    for window in window_list:
        if window['kCGWindowOwnerPID'] == active_pid:
            return window.get('kCGWindowName', 'Unknown')
    return None

get_active_window = {
    "Windows": get_active_window_windows,
    "Linux": get_active_window_linux,
    "Darwin": get_active_window_macos
}

# Save History


async def save_to_csv(tracked_windows, save_path, rotation_interval=timedelta(days=1)):
    current_time = datetime.now()
    rotation_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + rotation_interval

    # Determine the filename based on the rotation time
    date_str = current_time.strftime("%Y-%m-%d")
    filename = os.path.join(save_path, f"{date_str}.csv")

    # Check if the file already exists or create a new one
    file_exists = os.path.isfile(filename)

    # Use `asyncio.to_thread` to handle the file I/O in a separate thread without `async with`
    await asyncio.to_thread(write_to_csv_file, filename, tracked_windows, file_exists)

    return rotation_time  # Return the next rotation time


def write_to_csv_file(filename, tracked_windows, file_exists):
    """This helper function writes to a CSV file in a separate thread."""
    with open(filename, mode='a', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Time', 'Window Title'])
        writer.writerows(tracked_windows)


# Summary


def csv_to_summary(filename: str) -> Dict[str, timedelta]:
    with open(filename, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)[1:]  # Skip header

    # Time handling
    def get_duration(time_current, time_next):
        time_current = datetime.strptime(time_current, '%H:%M:%S')
        time_next = datetime.strptime(time_next, '%H:%M:%S')
        return time_next - time_current

    summary = {
        data[i][1].replace("–", "-").replace("—", "-"): get_duration(data[i][0], data[i + 1][0])
        for i in range(len(data) - 1)
    }

    return summary


def csv_to_event_format(filename: str) -> List[Tuple[timedelta, List[str]]]:
    with open(filename, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)[1:]  # Skip header

    # Time handling
    def get_duration(time_current, time_next):
        time_current = datetime.strptime(time_current, '%H:%M:%S')
        time_next = datetime.strptime(time_next, '%H:%M:%S')
        return time_next - time_current

    return [(get_duration(data[i][0], data[i + 1][0]), data[i][1].replace("–", "-").replace("—", "-").split(" - ")) for i in range(len(data) - 1)]


def summary_to_event_format(summary: Dict[str, timedelta]) -> List[Tuple[timedelta, str]]:
    return [(v, k.split(" - ")) for k,v in summary.items()]


def format_events(events: List[Tuple[timedelta, str]]) -> str:
    # Step 3: Organize events into hierarchical structure
    def add_to_hierarchy(hierarchy, hierarchy_list, duration):
        for part in hierarchy_list:
            hierarchy = hierarchy.setdefault(part, OrderedDict())
        try:
            hierarchy[hierarchy_list[-1]] = hierarchy.get(hierarchy_list[-1], timedelta()) + duration
        except Exception as e:
            if DEBUG:
                print(f"{e}")
                print(f"{hierarchy_list[-1]=} | {type(hierarchy_list[-1])=}")

    hierarchy = OrderedDict()
    for duration, program_hierarchy in events:
        add_to_hierarchy(hierarchy, list(reversed(program_hierarchy)), duration)

    def generate_prefix(depth: int) -> str:
        """generate the prefix to create a easy to read summary"""
        if depth == 0:
            return ""
        else:
            return "|" + "--" * (depth-1) + "> "

    # Step 5: Format the hierarchical structure into a string
    def format_hierarchy(hierarchy, depth=0):
        output = ""

        # Sort the hierarchy by duration in descending order
        sorted_items = sorted(hierarchy.items(), key=lambda item: calculate_total_duration(item[1]) if isinstance(item[1], OrderedDict) else item[1], reverse=True)

        for key, value in sorted_items:
            if isinstance(value, timedelta):
                # Base case: value is a timedelta, so just print it
                output += f"{generate_prefix(depth)}{str(value).split('.')[0]} - {key}\n"
            else:
                # Check if the level only has one child
                if len(value) == 1:
                    # Combine this level with its child
                    child_key, child_value = next(iter(value.items()))
                    if key != child_key:
                        combined_key = f"{key} - {child_key}"
                    else:
                        combined_key = key
                    if isinstance(child_value, timedelta):
                        output += f"{generate_prefix(depth)}{str(child_value).split('.')[0]} - {combined_key}\n"
                    else:
                        # Recurse with the combined key
                        value = OrderedDict([(combined_key, child_value)])
                        output += format_hierarchy(value, depth)
                else:
                    # Recursive case: value is a nested OrderedDict
                    total_duration = calculate_total_duration(value)
                    output += f"{generate_prefix(depth)}{str(total_duration).split('.')[0]} - {key}\n"
                    output += format_hierarchy(value, depth + 1)

        return output

    def calculate_total_duration(hierarchy):
        total_duration = timedelta()

        for value in hierarchy.values():
            if isinstance(value, timedelta):
                # If the value is a timedelta, add it to the total_duration
                total_duration += value
            else:
                # If the value is an OrderedDict, recursively calculate its total duration
                total_duration += calculate_total_duration(value)

        return total_duration

    formatted_output = format_hierarchy(hierarchy)
    return formatted_output.strip()


# Telegram integration


async def send_telegram_message(message_text):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message_text)
    await bot.session.close()


# Main


def main(path=f'{get_script_directory()}/window_tracking', add_to_calendar=False):
    root = tk.Tk()
    app = TrackingApp(root, path, add_to_calendar)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    fire.Fire(main)
