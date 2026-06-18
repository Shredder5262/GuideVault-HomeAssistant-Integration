# GuideVault Home Assistant Integration v0.5.8

This custom integration reads GuideVault's `/api/home-assistant/status` endpoint and queues reader commands through `/api/home-assistant/command`.

## Fixed in v0.5.8

- Restores the setup/options form fields:
  - GuideVault URL
  - Command token
  - Entity prefix
  - Polling interval
  - Enable reader control entities
  - Enable background control entities
- Fixes the data coordinator setup pattern for newer Home Assistant releases.
- Keeps diagnostics out of the package to avoid the stale `custom_components.guidevault.diagnostics` import path.
- Keeps all reader controls from v0.5.7:
  - First/Previous/Next/Last page
  - Toggle Overlay
  - Toggle Fullscreen
  - Fullscreen switch and sensor
  - Close Reader
  - Zoom In/Out and Zoom slider
  - Page number control
  - Reader Background select
  - Next/Previous Background
  - Background Brightness slider
  - Version/status sensors
- Keeps fallback services such as `guidevault.next_page`, `guidevault.toggle_fullscreen`, `guidevault.close_reader`, and `guidevault.set_background_brightness`.

## Important cleanup for failed v0.5.7 installs

If Home Assistant logs mention `custom_components.guidevault.diagnostics`, delete the old integration folder before installing this package. The v0.5.8 package intentionally does not contain `diagnostics.py`, but a failed or overlaid install can leave stale files behind.

Recommended cleanup:

1. Stop Home Assistant.
2. Delete `/config/custom_components/guidevault`.
3. Copy this package's `custom_components/guidevault` folder into `/config/custom_components/guidevault` or reinstall through HACS.
4. Start Home Assistant.
5. Remove and re-add the GuideVault integration if the old config entry still looks broken.

## Expected entities

- `sensor.guidevault_integration_version`
- `sensor.guidevault_server_version`
- `sensor.guidevault_reader`
- `sensor.guidevault_current_item`
- `sensor.guidevault_current_item_kind`
- `sensor.guidevault_page`
- `sensor.guidevault_page_count`
- `sensor.guidevault_progress_percent`
- `sensor.guidevault_zoom`
- `sensor.guidevault_display_mode`
- `sensor.guidevault_background`
- `sensor.guidevault_background_brightness_state`
- `binary_sensor.guidevault_fullscreen`
- `switch.guidevault_fullscreen`
- `select.guidevault_display_mode`
- `select.guidevault_reader_background`
- `number.guidevault_page`
- `number.guidevault_zoom`
- `number.guidevault_background_brightness`
- `button.guidevault_first_page`
- `button.guidevault_previous_page`
- `button.guidevault_next_page`
- `button.guidevault_last_page`
- `button.guidevault_toggle_overlay`
- `button.guidevault_toggle_fullscreen`
- `button.guidevault_close_reader`
- `button.guidevault_zoom_in`
- `button.guidevault_zoom_out`
- `button.guidevault_next_background`
- `button.guidevault_previous_background`

## Requirement

The installed background dropdown needs GuideVault 0.9.215 or newer so `/api/home-assistant/status` returns `availableBackgrounds`.
