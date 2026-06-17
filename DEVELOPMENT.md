# Development notes

## Expected GuideVault endpoint

```text
POST /api/home-assistant/command
```

## Confirmed command actions

```text
status
open
open_manual
open_strategy_guide
open_magazine
next_page
previous_page
first_page
last_page
set_page
zoom_in
zoom_out
set_zoom
set_display_mode
toggle_overlay
close_reader
```

## Payload

```json
{
  "action": "next_page",
  "itemTitle": "",
  "itemKind": "",
  "issueNumber": "",
  "volume": "",
  "page": 0,
  "zoom": 0,
  "displayMode": "",
  "background": "",
  "backgroundBrightness": 0
}
```
