# Development notes

## Validate in Home Assistant

1. Copy `custom_components/guidevault` into `/config/custom_components/guidevault`.
2. Restart Home Assistant.
3. Add GuideVault from the integrations UI.
4. Test service calls from Developer Tools > Actions.

## Expected GuideVault command endpoint

```text
POST /api/home-assistant/command
Content-Type: application/json
```

Example:

```json
{
  "command_action": "open",
  "item_title": "Super Mario 64",
  "content_type": "manual"
}
```
