"""
Unit Tests for Agent Utilities
"""
import pytest
from backend.agents.utils import format_history

def test_format_history_empty():
    assert format_history([]) == "No previous conversation."

def test_format_history_single_turn():
    history = [{"role": "user", "content": "Hello"}]
    expected = "Customer: Hello"
    assert format_history(history) == expected

def test_format_history_multiple_turns():
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    expected = "Customer: Hello\nAssistant: Hi there!"
    assert format_history(history) == expected

def test_format_history_respects_last_n():
    history = [
        {"role": "user", "content": "Turn 1"},
        {"role": "assistant", "content": "Turn 2"},
        {"role": "user", "content": "Turn 3"},
        {"role": "assistant", "content": "Turn 4"},
    ]
    expected = "Customer: Turn 3\nAssistant: Turn 4"
    assert format_history(history, last_n=2) == expected

def test_format_history_with_missing_keys():
    history = [{"role": "user"}, {"content": "Hi"}]
    expected = "Customer: \nAssistant: Hi"
    assert format_history(history) == expected
