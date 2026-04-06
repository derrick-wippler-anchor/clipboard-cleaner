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
import re

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
        print("  Monitoring clipboard for trailing whitespace and wrapped URLs...")
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

    def is_wrapped_url(self, text):
        """Check if text appears to be a single URL that got wrapped across lines."""
        if not text or '\n' not in text:
            return False

        # Strip and check if it starts with http:// or https://
        stripped = text.lstrip()
        if not (stripped.startswith('http://') or stripped.startswith('https://')):
            return False

        lines = text.split('\n')

        # Reasonable limits: not too many lines, not too long
        if len(lines) > 10 or len(text) > 10000:
            return False

        # Check for blank lines (would indicate separate content)
        if any(line.strip() == '' for line in lines):
            return False

        return True

    def join_url_lines(self, text):
        """Join URL lines together, removing newlines and extra whitespace."""
        lines = text.split('\n')
        # Strip leading/trailing whitespace from each line and join
        joined = ''.join(line.strip() for line in lines)
        return joined

    def clean_text(self, text):
        """Remove trailing whitespace from each line, and join wrapped URLs.
        Returns tuple of (cleaned_text, was_url_joined)."""
        # First, remove trailing whitespace
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        cleaned = '\n'.join(cleaned_lines)

        # Then check if it's a wrapped URL and join if so
        was_url_joined = False
        if self.is_wrapped_url(cleaned):
            cleaned = self.join_url_lines(cleaned)
            was_url_joined = True

        return cleaned, was_url_joined

    def has_trailing_whitespace(self, text):
        """Check if text has any trailing whitespace."""
        lines = text.split('\n')
        return any(line != line.rstrip() for line in lines)

    def needs_cleaning(self, text):
        """Check if text needs any cleaning (whitespace or URL joining)."""
        if not text:
            return False
        # Check for trailing whitespace
        if self.has_trailing_whitespace(text):
            return True
        # Check for wrapped URLs
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        cleaned = '\n'.join(cleaned_lines)
        if self.is_wrapped_url(cleaned):
            return True
        return False

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
                        if current_text and self.needs_cleaning(current_text):
                            cleaned_text, was_url_joined = self.clean_text(current_text)
                            cleaned_hash = self.get_hash(cleaned_text)

                            # Only update if something actually changed
                            if cleaned_hash != current_hash:
                                # Debug: log the before/after to file
                                try:
                                    import os
                                    log_path = os.path.expanduser('~/clipboard-debug.log')
                                    with open(log_path, 'a') as f:
                                        f.write(f"{'='*70}\n")
                                        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                                        f.write(f"Action: {'URL joining' if was_url_joined else 'Whitespace removal'}\n")
                                        f.write(f"Original length: {len(current_text)} chars, {current_text.count(chr(10)) + 1} lines\n")
                                        f.write(f"Cleaned length: {len(cleaned_text)} chars, {cleaned_text.count(chr(10)) + 1} lines\n")
                                        f.write(f"\nORIGINAL:\n{repr(current_text)}\n")
                                        f.write(f"\nCLEANED:\n{repr(cleaned_text)}\n")
                                        f.write(f"{'='*70}\n\n")
                                except Exception as e:
                                    print(f"Debug logging error: {e}")

                                self.set_clipboard(cleaned_text)
                                self.last_cleaned_hash = cleaned_hash

                                # Report what was done
                                if was_url_joined:
                                    original_lines = current_text.count('\n') + 1
                                    print(f"✓ Cleaned wrapped URL from {original_lines} lines to 1 line")
                                else:
                                    original_lines = current_text.count('\n') + 1
                                    chars_removed = len(current_text) - len(cleaned_text)
                                    print(f"✓ Cleaned {original_lines} lines, removed {chars_removed} trailing spaces")
                        else:
                            # Debug: clipboard changed but doesn't need cleaning
                            if current_text:
                                try:
                                    import os
                                    log_path = os.path.expanduser('~/clipboard-debug.log')
                                    with open(log_path, 'a') as f:
                                        f.write(f"{'='*70}\n")
                                        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                                        f.write(f"Action: NO CLEANING NEEDED\n")
                                        f.write(f"Length: {len(current_text)} chars, {current_text.count(chr(10)) + 1} lines\n")
                                        f.write(f"Has trailing whitespace: {self.has_trailing_whitespace(current_text)}\n")
                                        # Check if it's a URL
                                        is_url = current_text.strip().startswith(('http://', 'https://'))
                                        f.write(f"Starts with http(s): {is_url}\n")
                                        f.write(f"Has newlines: {chr(10) in current_text}\n")
                                        f.write(f"\nCONTENT:\n{repr(current_text)}\n")
                                        f.write(f"{'='*70}\n\n")
                                    print(f"⊘ Clipboard changed but no cleaning needed ({len(current_text)} chars, {current_text.count(chr(10)) + 1} lines)")
                                except Exception as e:
                                    print(f"Debug logging error: {e}")

                    self.last_hash = current_hash

                # Sleep to avoid high CPU usage
                time.sleep(0.5)

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
