"""
Tests for RedditMonitor real-mode behavior.
"""
import pytest
from datetime import datetime

from agents.red_queen import RedditMonitor
from config.settings import config


@pytest.mark.asyncio
async def test_reddit_monitor_dedupes_pain_points():
    monitor = RedditMonitor()
    
    # Same post analyzed twice should dedupe
    post = {
        "title": "Why is it so hard to find EV charger rebates?",
        "selftext": "",
        "score": 100,
        "num_comments": 20,
        "created_utc": datetime.now().timestamp(),
        "permalink": "/r/evcharging/comments/abc123"
    }
    
    p1 = monitor._analyze_post("evcharging", post)
    p2 = monitor._analyze_post("evcharging", post)
    
    assert p1 is not None
    assert p2 is not None
    assert monitor._dedupe(p1) is True
    assert monitor._dedupe(p2) is False


def test_reddit_monitor_matches_ev_patterns():
    monitor = RedditMonitor()
    
    post = {
        "title": "Best Level 2 charger rebate in California?",
        "selftext": "",
        "score": 50,
        "num_comments": 10,
        "created_utc": datetime.now().timestamp(),
        "permalink": "/r/evcharging/comments/def456"
    }
    
    result = monitor._analyze_post("evcharging", post)
    assert result is not None
    assert "rebate" in result.text.lower()


def test_reddit_monitor_matches_pain_patterns():
    monitor = RedditMonitor()
    
    post = {
        "title": "Hard to find all the EV incentives in one place",
        "selftext": "",
        "score": 30,
        "num_comments": 5,
        "created_utc": datetime.now().timestamp(),
        "permalink": "/r/electricvehicles/comments/ghi789"
    }
    
    result = monitor._analyze_post("electricvehicles", post)
    assert result is not None
    assert result.source == "reddit:r/electricvehicles"


def test_reddit_monitor_ignores_irrelevant_posts():
    monitor = RedditMonitor()
    
    post = {
        "title": "Just bought a new Tesla Model 3",
        "selftext": "Love the car!",
        "score": 200,
        "num_comments": 50,
        "created_utc": datetime.now().timestamp(),
        "permalink": "/r/TeslaLounge/comments/jkl012"
    }
    
    result = monitor._analyze_post("TeslaLounge", post)
    assert result is None
