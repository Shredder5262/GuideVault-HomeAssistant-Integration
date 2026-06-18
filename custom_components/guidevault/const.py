"""Constants for the GuideVault Home Assistant integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "guidevault"
NAME = "GuideVault"
VERSION = "0.5.8"

CONF_BASE_URL = "base_url"
CONF_COMMAND_TOKEN = "command_token"
CONF_ENTITY_PREFIX = "entity_prefix"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_CONTROLS = "enable_controls"
CONF_ENABLE_BACKGROUND_CONTROLS = "enable_background_controls"

DEFAULT_BASE_URL = "http://localhost:5478"
DEFAULT_ENTITY_PREFIX = "guidevault"
DEFAULT_SCAN_INTERVAL_SECONDS = 5
DEFAULT_ENABLE_CONTROLS = True
DEFAULT_ENABLE_BACKGROUND_CONTROLS = True

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
]

DISPLAY_MODE_OPTIONS: dict[str, str] = {
    "1 page": "single_page",
    "2 page": "two_page",
    "2 page adaptive": "adaptive_two_page",
}

DISPLAY_MODE_LABELS: dict[str, str] = {value: key for key, value in DISPLAY_MODE_OPTIONS.items()}

COMMAND_ACTIONS: dict[str, str] = {
    "first_page": "first_page",
    "previous_page": "previous_page",
    "next_page": "next_page",
    "last_page": "last_page",
    "toggle_overlay": "toggle_overlay",
    "toggle_fullscreen": "toggle_fullscreen",
    "close_reader": "close_reader",
    "zoom_in": "zoom_in",
    "zoom_out": "zoom_out",
    "next_background": "next_background",
    "previous_background": "previous_background",
}
