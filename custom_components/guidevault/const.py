"""Constants for the GuideVault Home Assistant integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "guidevault"
NAME = "GuideVault"
VERSION = "0.5.5"

CONF_BASE_URL = "base_url"
CONF_COMMAND_TOKEN = "command_token"

DEFAULT_BASE_URL = "http://localhost:5478"
DEFAULT_SCAN_INTERVAL_SECONDS = 5

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.NUMBER,
]

DISPLAY_MODE_OPTIONS: dict[str, str] = {
    "1 page": "single_page",
    "2 page": "two_page",
    "2 page adaptive": "adaptive_two_page",
}

DISPLAY_MODE_LABELS: dict[str, str] = {value: key for key, value in DISPLAY_MODE_OPTIONS.items()}
