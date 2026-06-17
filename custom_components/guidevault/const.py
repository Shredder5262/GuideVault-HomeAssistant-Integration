"""Constants for the GuideVault Home Assistant integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "guidevault"
PLATFORMS: list[Platform] = [Platform.BUTTON]

DEFAULT_NAME = "GuideVault"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5478
DEFAULT_TIMEOUT = 10

CONF_API_KEY = "api_key"
CONF_SSL = "ssl"
CONF_VERIFY_SSL = "verify_ssl"
CONF_TIMEOUT = "timeout"

DATA_CLIENTS = "clients"
DATA_SERVICES_REGISTERED = "services_registered"

COMMAND_ENDPOINT = "/api/home-assistant/command"

SERVICE_COMMAND = "command"
SERVICE_OPEN_ITEM = "open_item"
SERVICE_NEXT_PAGE = "next_page"
SERVICE_PREVIOUS_PAGE = "previous_page"
SERVICE_FIRST_PAGE = "first_page"
SERVICE_LAST_PAGE = "last_page"
SERVICE_GO_TO_PAGE = "go_to_page"
SERVICE_TOGGLE_FULLSCREEN = "toggle_fullscreen"
SERVICE_SET_BACKGROUND = "set_background"
SERVICE_CLOSE_READER = "close_reader"

ACTION_OPEN = "open"
ACTION_PAGE_NEXT = "page_next"
ACTION_PAGE_PREVIOUS = "page_previous"
ACTION_PAGE_FIRST = "page_first"
ACTION_PAGE_LAST = "page_last"
ACTION_PAGE_GOTO = "page"
ACTION_TOGGLE_FULLSCREEN = "toggle_fullscreen"
ACTION_SET_BACKGROUND = "set_background"
ACTION_CLOSE = "close"

CONTENT_TYPES = ["auto", "manual", "strategy_guide", "strategy-guide", "magazine"]
