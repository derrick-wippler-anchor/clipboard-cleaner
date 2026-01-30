#!/usr/bin/env python3
"""
Clipboard Monitor - Automatically cleans trailing whitespace from clipboard.
Runs in the background and monitors clipboard changes.
Usage: Run the script and it will automatically clean any text you copy.
       Press Ctrl+C to stop.
"""

import subprocess
import time
import sys
import hashlib

class ClipboardMonitor:
    def __init__(self):
        self.clipboard_util = self.detect_clipboard_util()
        if not self.clipboard_util:
            print("ERROR: No clipboard utility found.")
            print("Please install: sudo apt install xclip")
            print("or for Wayland: sudo apt install wl-clipboard")
            sys.exit(1)

        self.last_hash = None
        self.last_cleaned_hash = None
        print(f"✓ Clipboard monitor started (using {self.clipboard_util})")
        print("  Monitoring clipboard for trailing whitespace...")
        print("  Press Ctrl+C to stop")

    def detect_clipboard_util(self):
        """Detect which clipboard utility is available."""
        try:
            subprocess.run(['xclip', '-version'], capture_output=True, check=True)
            return 'xclip'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        try:
            subprocess.run(['wl-paste', '--version'], capture_output=True, check=True)
            return 'wayland'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return None

    def get_clipboard(self):
        """Get current clipboard content."""
        try:
            if self.clipboard_util == 'xclip':
                result = subprocess.run(
                    ['xclip', '-o', '-selection', 'clipboard'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
            else:  # wayland
                result = subprocess.run(
                    ['wl-paste'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
            return result.stdout if result.returncode == 0 else None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    def set_clipboard(self, text):
        """Set clipboard content."""
        try:
            if self.clipboard_util == 'xclip':
                process = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE
                )
            else:  # wayland
                process = subprocess.Popen(
                    ['wl-copy'],
                    stdin=subprocess.PIPE
                )
            process.communicate(text.encode('utf-8'), timeout=1)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def clean_text(self, text):
        """Remove trailing whitespace from each line."""
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        return '\n'.join(cleaned_lines)

    def has_trailing_whitespace(self, text):
        """Check if text has any trailing whitespace."""
        lines = text.split('\n')
        return any(line != line.rstrip() for line in lines)

    def get_hash(self, text):
        """Get hash of text for comparison."""
        if text is None:
            return None
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def monitor(self):
        """Monitor clipboard and clean when needed."""
        while True:
            try:
                # Get current clipboard
                current_text = self.get_clipboard()
                current_hash = self.get_hash(current_text)

                # Check if clipboard changed
                if current_hash and current_hash != self.last_hash:
                    # Don't clean if we just set this value
                    if current_hash != self.last_cleaned_hash:
                        # Check if it needs cleaning
                        if current_text and self.has_trailing_whitespace(current_text):
                            cleaned_text = self.clean_text(current_text)
                            cleaned_hash = self.get_hash(cleaned_text)

                            # Only update if something actually changed
                            if cleaned_hash != current_hash:
                                self.set_clipboard(cleaned_text)
                                self.last_cleaned_hash = cleaned_hash

                                # Count lines and characters removed
                                lines = current_text.count('\n') + 1
                                chars_removed = len(current_text) - len(cleaned_text)
                                print(f"✓ Cleaned {lines} lines, removed {chars_removed} trailing spaces")

                    self.last_hash = current_hash

                # Sleep to avoid high CPU usage
                time.sleep(0.3)

            except KeyboardInterrupt:
                print("\n✓ Clipboard monitor stopped")
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                time.sleep(1)

def main():
    monitor = ClipboardMonitor()
    monitor.monitor()

if __name__ == "__main__":
    main()
