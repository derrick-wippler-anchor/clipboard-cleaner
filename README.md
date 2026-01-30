# Clipboard Cleaner

A lightweight background utility for Chromebooks that automatically removes trailing whitespace from text copied to your clipboard.

## Why This Exists

The ChromeOS built-in terminal (Crostini) has a known issue where copying multi-line text includes trailing whitespace that extends to the terminal width. When you paste this text into other applications like code editors, text documents, or web forms, you get unwanted spaces at the end of each line.

This is a common problem across many terminal emulators - terminals pad each line with spaces to fill the terminal width when copying to the clipboard. This utility solves the problem by monitoring your clipboard and automatically stripping these trailing spaces, allowing you to copy code, commands, or text from your terminal without manual cleanup.

## Features

- Monitors clipboard changes in real-time
- Automatically strips trailing whitespace from each line
- Minimal CPU usage with efficient change detection
- Visual feedback showing cleaned lines and characters removed
- Designed for ChromeOS Linux environment

## Requirements

- Python 3.6+
- `xclip` clipboard utility

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd clipboard-cleaner
```

2. Install xclip:
```bash
sudo apt install xclip
```

## Usage

Run the script to start monitoring your clipboard:

```bash
./clipboard-cleaner.py
```

Or:

```bash
python3 clipboard-cleaner.py
```

The script will run in the background and automatically clean any text you copy. Press `Ctrl+C` to stop.

### Running at Startup

To run automatically at system startup, add the script to your startup applications or create a systemd user service.

## How It Works

The script continuously monitors your system clipboard for changes. When new text is detected, it:

1. Checks if the text contains trailing whitespace
2. Removes trailing whitespace from each line
3. Updates the clipboard with the cleaned text
4. Displays statistics about the cleaning operation

The script uses MD5 hashing to avoid infinite loops and only cleans text once per copy operation.

## License

MIT
