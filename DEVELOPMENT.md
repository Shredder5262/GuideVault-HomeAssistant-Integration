# Development notes

## Expected GuideVault endpoints

```text
POST /api/home-assistant/command
GET  /api/home-assistant/status
```

## Command payload

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

## Local install test

1. Copy `custom_components/guidevault` into `/config/custom_components/guidevault`.
2. Restart Home Assistant.
3. Add the integration from the UI.
4. Test commands from Developer Tools > Actions.
5. Confirm status sensors update from `/api/home-assistant/status`.
