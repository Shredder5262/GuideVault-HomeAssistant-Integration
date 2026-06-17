# GuideVault Home Assistant Integration

This is a custom Home Assistant integration for controlling a local GuideVault server.

## Features

- UI config flow: `Settings > Devices & services > Add integration > GuideVault`
- Local GuideVault connection over HTTP or HTTPS
- Optional API key support through `Authorization: Bearer <token>`
- Reader control services
- Button entities for common reader controls
- HACS-ready repository structure

## Install manually

Copy the `custom_components/guidevault` folder into your Home Assistant config folder:

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

## HACS install later

Publish this repository with the following structure:

```text
custom_components/guidevault/
hacs.json
README.md
```

Then in HACS:

```text
HACS > Integrations > Three dots > Custom repositories
```

Add the GitHub repository URL and select category:

```text
Integration
```

## Services

### `guidevault.open_item`

Open a manual, strategy guide, or magazine.

```yaml
service: guidevault.open_item
data:
  item_title: "Super Mario 64"
  content_type: "manual"
```

Open a strategy guide:

```yaml
service: guidevault.open_item
data:
  item_title: "Super Mario 64"
  content_type: "strategy_guide"
```

Open a magazine issue:

```yaml
service: guidevault.open_item
data:
  item_title: "Nintendo Power"
  content_type: "magazine"
  issue: "1"
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

### `guidevault.set_background`

```yaml
service: guidevault.set_background
data:
  background: "dark"
```

### `guidevault.command`

Use this for raw GuideVault command payloads.

```yaml
service: guidevault.command
data:
  command_action: "open"
  item_title: "Super Mario 64"
  content_type: "manual"
```

## Dashboard example

See:

```text
examples/guidevault-remote-card.yaml
```

## Command mapping

The integration sends these `command_action` values to GuideVault:

| Home Assistant service | GuideVault `command_action` |
|---|---|
| `guidevault.open_item` | `open` |
| `guidevault.next_page` | `page_next` |
| `guidevault.previous_page` | `page_previous` |
| `guidevault.first_page` | `page_first` |
| `guidevault.last_page` | `page_last` |
| `guidevault.go_to_page` | `page` |
| `guidevault.toggle_fullscreen` | `toggle_fullscreen` |
| `guidevault.set_background` | `set_background` |
| `guidevault.close_reader` | `close` |

## Recommended GuideVault server endpoints

This integration currently uses:

```text
POST /api/home-assistant/command
```

For better future Home Assistant entities, GuideVault should also expose:

```text
GET /api/home-assistant/status
```

Recommended status payload:

```json
{
  "ok": true,
  "version": "1.0.0",
  "readerOpen": true,
  "currentTitle": "Super Mario 64",
  "contentType": "manual",
  "page": 12,
  "pageCount": 64,
  "fullscreen": false
}
```

That would allow a future version to add sensors such as current item, current page, reader state, and fullscreen state.
