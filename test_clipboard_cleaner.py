#!/usr/bin/env python3
"""
Unit tests for clipboard-cleaner URL joining functionality.
Run with: python3 test_clipboard_cleaner.py
"""

import unittest
import sys
import os

# Add the current directory to path to import the module
sys.path.insert(0, os.path.dirname(__file__))

# Import the ClipboardMonitor class
# We need to mock the clipboard utilities since we're just testing the logic
from unittest.mock import Mock, patch
import importlib.util

# Load the module from the hyphenated filename
spec = importlib.util.spec_from_file_location("clipboard_cleaner",
                                               os.path.join(os.path.dirname(__file__), "clipboard-cleaner.py"))
clipboard_module = importlib.util.module_from_spec(spec)

# Mock subprocess to avoid requiring xclip/wl-clipboard
with patch('subprocess.run') as mock_run:
    mock_run.return_value = Mock(returncode=0, stdout='')
    spec.loader.exec_module(clipboard_module)
    ClipboardMonitor = clipboard_module.ClipboardMonitor


class TestURLJoining(unittest.TestCase):
    """Test cases for URL joining functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the clipboard utility detection to avoid requiring xclip/wl-clipboard
        with patch.object(ClipboardMonitor, 'detect_clipboard_util', return_value='xclip'):
            with patch('builtins.print'):  # Suppress startup messages
                self.monitor = ClipboardMonitor()

    def test_wrapped_claude_oauth_url(self):
        """Test joining a wrapped Claude OAuth URL (real-world example)."""
        wrapped_url = """https://example.com/oauth/authorize?code=true&client_id=12345678-abcd-efgh-ijkl-mnopqrstuvwx&response_type=code&redirect_uri=https%3A%2F%2Fexample.com%2Foauth%2Fcallback&scope=read%3Aprofile+write%3Adata+manage%3Asessions+access%3Aresour
  ces&code_challenge=ABCD1234ExampleChallengeString5678WXYZ&code_challenge_method=S256&state=ExampleStateString123456789"""

        expected = "https://example.com/oauth/authorize?code=true&client_id=12345678-abcd-efgh-ijkl-mnopqrstuvwx&response_type=code&redirect_uri=https%3A%2F%2Fexample.com%2Foauth%2Fcallback&scope=read%3Aprofile+write%3Adata+manage%3Asessions+access%3Aresources&code_challenge=ABCD1234ExampleChallengeString5678WXYZ&code_challenge_method=S256&state=ExampleStateString123456789"

        result, was_url_joined = self.monitor.clean_text(wrapped_url)
        self.assertEqual(result, expected)
        self.assertNotIn('\n', result)
        self.assertTrue(was_url_joined)

    def test_simple_wrapped_url(self):
        """Test joining a simple wrapped URL."""
        wrapped_url = "https://example.com/path/to/resource\n?param=value&other=data"
        expected = "https://example.com/path/to/resource?param=value&other=data"

        result, was_url_joined = self.monitor.clean_text(wrapped_url)
        self.assertEqual(result, expected)
        self.assertTrue(was_url_joined)

    def test_wrapped_url_with_leading_whitespace(self):
        """Test joining a URL where continuation lines have leading whitespace."""
        wrapped_url = "https://example.com/api/endpoint\n  ?query=test\n  &param=value"
        expected = "https://example.com/api/endpoint?query=test&param=value"

        result, was_url_joined = self.monitor.clean_text(wrapped_url)
        self.assertEqual(result, expected)
        self.assertTrue(was_url_joined)

    def test_is_wrapped_url_detection(self):
        """Test that is_wrapped_url correctly identifies wrapped URLs."""
        # Should be detected as wrapped URL
        self.assertTrue(self.monitor.is_wrapped_url("https://example.com\n/path"))
        self.assertTrue(self.monitor.is_wrapped_url("http://example.com\n?query=test"))
        self.assertTrue(self.monitor.is_wrapped_url("  https://example.com\n/path"))

        # Should NOT be detected as wrapped URL
        self.assertFalse(self.monitor.is_wrapped_url("https://example.com"))  # No newlines
        self.assertFalse(self.monitor.is_wrapped_url("not a url\nwith newlines"))  # Not a URL
        self.assertFalse(self.monitor.is_wrapped_url("https://example.com\n\nhttps://other.com"))  # Blank line

    def test_multiple_urls_not_joined(self):
        """Test that multiple URLs on separate lines are NOT joined."""
        multiple_urls = "https://example.com/page1\n\nhttps://example.com/page2"

        # Should not be modified because there's a blank line
        result, was_url_joined = self.monitor.clean_text(multiple_urls)
        self.assertIn('\n', result)
        self.assertFalse(was_url_joined)

    def test_trailing_whitespace_removed(self):
        """Test that trailing whitespace is still removed."""
        text_with_trailing = "line one   \nline two  \nline three\t"
        expected = "line one\nline two\nline three"

        result, was_url_joined = self.monitor.clean_text(text_with_trailing)
        self.assertEqual(result, expected)
        self.assertFalse(was_url_joined)

    def test_trailing_whitespace_and_url_joining(self):
        """Test that both trailing whitespace removal and URL joining work together."""
        wrapped_url_with_trailing = "https://example.com/path   \n  ?param=value  "
        expected = "https://example.com/path?param=value"

        result, was_url_joined = self.monitor.clean_text(wrapped_url_with_trailing)
        self.assertEqual(result, expected)
        self.assertTrue(was_url_joined)

    def test_non_url_multiline_text_unchanged(self):
        """Test that normal multi-line text is not affected (except trailing whitespace)."""
        normal_text = "This is a normal\nmulti-line text\nwith multiple lines"

        result, was_url_joined = self.monitor.clean_text(normal_text)
        # Should still have newlines, just trailing whitespace removed
        self.assertEqual(result.count('\n'), 2)
        self.assertEqual(result, normal_text)
        self.assertFalse(was_url_joined)

    def test_url_too_many_lines_not_joined(self):
        """Test that URLs with too many lines (>10) are not joined."""
        # Create a URL with 11 lines
        lines = ["https://example.com"] + [f"line{i}" for i in range(10)]
        long_url = "\n".join(lines)

        result, was_url_joined = self.monitor.clean_text(long_url)
        # Should still have newlines because it exceeds the limit
        self.assertIn('\n', result)
        self.assertFalse(was_url_joined)

    def test_needs_cleaning_detection(self):
        """Test that needs_cleaning correctly identifies text that needs processing."""
        # Should need cleaning - trailing whitespace
        self.assertTrue(self.monitor.needs_cleaning("text with trailing   "))

        # Should need cleaning - wrapped URL
        self.assertTrue(self.monitor.needs_cleaning("https://example.com\n/path"))

        # Should NOT need cleaning
        self.assertFalse(self.monitor.needs_cleaning("clean text"))
        self.assertFalse(self.monitor.needs_cleaning("https://example.com/path"))


def run_tests():
    """Run all tests and print results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestURLJoining)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("="*70)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
