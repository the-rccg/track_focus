# Window Tracking App

Welcome to the **Window Tracking App** designed to help you remember what you have worked on all day! This application is designed to monitor and log the active windows on your computer, providing a detailed summary of how your time is spent across different applications and give a detailed hierarchical summary.

The app also supports integration with Telegram to send session summaries directly to your chat, and Google Calendar integration coming soon!

## Features

- **Cross-Platform Support:** Works on Windows, Linux, and macOS, automatically detecting the operating system.
- **Real-Time Tracking:** Monitors active windows in real-time, logging the window title and timestamp.
- **Daily Rotation of Logs:** Automatically saves the tracked windows into daily CSV files, keeping your logs organized.
- **Hierarchical Summary:** Provides a structured, easy-to-read summary of the time spent on each window or application.
- **Telegram Notifications:** Optionally sends the session summary to a specified Telegram chat.

## Installation

To get started, you'll need to have Python installed along with a few dependencies. Follow the steps below to set up the app:

### Dependencies

Install the required Python packages using pip:

```bash
pip install asyncio aiogram fire pygetwindow Xlib Quartz AppKit
```

### Telegram Setup (Optional)

1. Create a `telegram.json` file in the root directory of the project.
2. Include your bot's token and chat ID in the following format:

```json
{
    "telegram": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
}
```

This will allow the app to send summaries to your Telegram chat.

## Usage

To run the app, simply execute the `main` function from the command line:

```bash
python tracking_app.py
```

The app will open a small window with a button to start or stop tracking. The window will always stay on top, ensuring easy access.

### Command-Line Arguments

- **path:** Specify a custom directory for saving the logs. Defaults to a `window_tracking` folder in the script directory.
- **add_to_calendar:** Set this flag to integrate tracking data with your calendar (feature under development).

Example:

```bash
python tracking_app.py --path="your/custom/path"
```

## How It Works

### Tracking Active Windows

The app monitors the currently active window on your system, recording its title and the time it was active. It supports different methods for getting the active window based on the operating system:

- **Windows:** Uses the `pygetwindow` library.
- **Linux:** Utilizes the Xlib display manager.
- **macOS:** Leverages the Quartz framework and AppKit to retrieve the active window.

### Data Saving

The app saves the tracked windows into CSV files, which are rotated daily. It maintains a summary of the time spent on each window, formatted into a hierarchical structure to show which applications and tasks took up the most time.

### Telegram Integration

At the end of a tracking session, the app can send a summary of your activity to a Telegram chat. This feature is particularly useful if you want to keep track of your productivity remotely.

## Use Case: Daily Productivity Tracking

This app is particularly helpful in keeping track of what you have accomplished throughout the day. By monitoring your active windows, you can easily review which tasks consumed the most time and where your focus was directed. This makes the end-of-day wrap-up work much easier, allowing you to reflect on your productivity and plan for the next day.

## Contributing

Contributions are welcome! Feel free to fork the repository, create a new branch, and submit a pull request. Please ensure your code is well-documented and follows the existing style.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

---

Thank you for using the Window Tracking App! We hope it helps you better manage your time and productivity. If you encounter any issues or have suggestions for new features, don't hesitate to open an issue or reach out to us.

