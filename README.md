# GuideVault Home Assistant Integration

Home Assistant custom integration for controlling a local GuideVault server.

## Features

- UI config flow
- HACS-ready repository structure
- Local HTTP/HTTPS GuideVault connection
- Optional API key support through `Authorization: Bearer <token>`
- Reader control button entities
- Status sensors for the active GuideVault reader
- Services/actions that match GuideVault's existing REST command payload

## Install manually

Copy:

```text
custom_components/guidevault
```

to:

```text
/config/custom_components/guidevault
```

Restart Home Assistant, then add the integration from:

```text
Settings > Devices & services > Add integration > GuideVault
```

Example GuideVault URL:

```text
http://192.168.1.10:5478
```

## HACS install

Add this GitHub repository to HACS as a custom repository of type:

```text
Integration
```

## Status sensors

The integration adds sensors for:

- Currently reading
- Reader state
- Content type
- Page
- Page count
- Zoom
- Display mode
- Background
- Background brightness
- Fullscreen
- Version

These sensors read:

```text
GET /api/home-assistant/status
```

If your GuideVault build does not expose that endpoint yet, the command buttons can still work, but status sensors will be unavailable until the server adds it.

Recommended GuideVault status response:

```json
{
  "ok": true,
  "version": "1.0.0",
  "readerOpen": true,
  "currentTitle": "Super Mario 64",
  "contentType": "manual",
  "page": 12,
  "pageCount": 64,
  "zoom": 1.0,
  "displayMode": "single",
  "background": "dark",
  "backgroundBrightness": 50,
  "fullscreen": false
}
```

## Command payload

The integration sends GuideVault's existing REST command format:

```json
{
  "action": "open",
  "itemTitle": "Super Mario 64",
  "itemKind": "manual",
  "issueNumber": "",
  "volume": "",
  "page": 0,
  "zoom": 0,
  "displayMode": "",
  "background": "",
  "backgroundBrightness": 0
}
```

## Services/actions

### `guidevault.open_item`

```yaml
service: guidevault.open_item
data:
  item_title: "Super Mario 64"
  item_kind: "manual"
```

Strategy guide:

```yaml
service: guidevault.open_item
data:
  item_title: "Super Mario 64"
  item_kind: "strategyGuide"
```

Magazine issue:

```yaml
service: guidevault.open_item
data:
  item_title: "Nintendo Power"
  item_kind: "magazine"
  issue_number: "1"
```

### Reader controls

```yaml
service: guidevault.next_page
```

```yaml
service: guidevault.previous_page
```

```yaml
service: guidevault.first_page
```

```yaml
service: guidevault.last_page
```

```yaml
service: guidevault.go_to_page
data:
  page: 12
```

```yaml
service: guidevault.toggle_fullscreen
```

```yaml
service: guidevault.close_reader
```

### Reader settings

```yaml
service: guidevault.set_zoom
data:
  zoom: 1.25
```

```yaml
service: guidevault.set_display_mode
data:
  display_mode: "single"
```

```yaml
service: guidevault.set_background
data:
  background: "dark"
```

```yaml
service: guidevault.set_background_brightness
data:
  background_brightness: 50
```

### Raw command

Use `guidevault.command` for the full REST payload.

```yaml
service: guidevault.command
data:
  action: "open"
  item_title: "Super Mario 64"
  item_kind: "manual"
  issue_number: ""
  volume: ""
  page: 0
  zoom: 0
  display_mode: ""
  background: ""
  background_brightness: 0
```

Backward-compatible aliases are accepted:

- `command_action` -> `action`
- `content_type` -> `itemKind`
- `issue` -> `issueNumber`

## Dashboard examples

See:

```text
examples/guidevault-remote-card.yaml
examples/guidevault-status-card.yaml
```

## If commands return 404

Confirm the configured command endpoint in integration options. Default:

```text
/api/home-assistant/command
```

A 404 usually means the GuideVault server build does not expose the endpoint, the base URL is wrong, or a reverse proxy is routing the request away from GuideVault.


## v0.2.1 note

Fixes host normalization when the config form is filled as:

```text
Host or URL: http://192.168.1.20
Port: 5478
```

Earlier builds could drop the separate port when the host field included `http://`, causing commands to hit port 80 instead of GuideVault's port.


## v0.3.0 note

Adds Home Assistant `select` and `number` entities for reader settings:

- Background dropdown
- Display mode dropdown
- Background brightness slider
- Zoom number control

Status parsing is more flexible and now looks for several common GuideVault status field names. The integration also tries common version/info endpoints if `/api/home-assistant/status` does not include a version value.


## v0.4.0 note

Changes the default control action names to match the original GuideVault REST command style:

| Control | Action sent |
|---|---|
| Next page | `next` |
| Previous page | `previous` |
| First page | `first` |
| Last page | `last` |
| Toggle fullscreen | `fullscreen` |
| Zoom | `zoom` |
| Background | `background` |
| Background brightness | `backgroundBrightness` |
| Display mode | `displayMode` |

The integration now sends `action`, `command_action`, and `commandAction` in the payload for compatibility with old and new GuideVault handlers.

Display mode options are limited to:

- `1 page`
- `2 page`
- `2 page adaptive`

Background options are read from the GuideVault status response when the server exposes installed/available backgrounds. If the status API does not expose installed backgrounds yet, Home Assistant can only show fallback options.
