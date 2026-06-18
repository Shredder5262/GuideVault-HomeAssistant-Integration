# GuideVault Home Assistant Integration

Home Assistant custom integration for controlling a local GuideVault server.

## v0.5.0 correction

This release uses only the GuideVault REST command actions that were confirmed working:

- `status`
- `open`
- `open_manual`
- `open_strategy_guide`
- `open_magazine`
- `next_page`
- `previous_page`
- `first_page`
- `last_page`
- `set_page`
- `zoom_in`
- `zoom_out`
- `set_zoom`
- `set_display_mode`
- `toggle_overlay`
- `close_reader`

The integration sends the original GuideVault REST payload shape:

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

## Features

- UI config flow
- HACS-ready repository structure
- Optional API key support through both `Authorization: Bearer <token>` and `X-Api-Key`
- Reader control button entities
- Status sensors for the active GuideVault reader
- Display mode select: `1 page`, `2 page`, `2 page adaptive`
- Zoom number entity
- Raw command service for direct GuideVault action testing

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
http://192.168.1.20:5478
```

or:

```text
Host or URL: 192.168.1.20
Port: 5478
Use HTTPS: unchecked
```

## Background controls

Background and background brightness are reported as sensors if GuideVault status exposes them, but active controls were removed in v0.5.0 because those commands were not part of the confirmed working REST command list. Add them back after GuideVault exposes working actions for them.


## v0.5.1

- Fixed Home Assistant `hass.helpers` button press error by using `async_call_later`.
- Added active `Toggle fullscreen` button entity as a compatibility alias for `toggle_overlay`.
- Restored active background and background brightness controls.
- Background controls send `set_background` and `set_background_brightness`; these still require matching GuideVault server-side command support.


## v0.5.2

- Removes the broken Toggle fullscreen button entity. Use Toggle overlay instead.
- Display mode now defaults to `2 page` when GuideVault status does not report a value.
- Background selector now recursively discovers background lists from nested status payloads and filters `unknown`/`unavailable`.
- Background brightness control uses box mode instead of slider mode to avoid Home Assistant opening the more-info dialog when dragging to 0.
- Removes redundant background/background brightness sensors; the select and number entities are the active state/control surfaces.
- Reorders the remote card so Close reader sits with the other reader buttons.
