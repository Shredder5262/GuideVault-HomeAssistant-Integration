# GuideVault Home Assistant Integration v0.5.7

This custom integration reads GuideVault's `/api/home-assistant/status` endpoint and queues reader commands through `/api/home-assistant/command`.

## Fixed in v0.5.7

This release makes the GuideVault reader controls explicit across Home Assistant platforms and services:

- Adds/restores page control buttons:
  - First Page
  - Previous Page
  - Next Page
  - Last Page
- Adds/restores reader control buttons:
  - Toggle Overlay
  - Toggle Fullscreen
  - Close Reader
  - Zoom In
  - Zoom Out
- Adds/restores background controls:
  - Reader Background select
  - Next Background button
  - Previous Background button
  - Background Brightness number slider
- Adds a controllable Fullscreen switch in addition to the Fullscreen binary sensor.
- Adds status/version sensors:
  - Integration Version
  - Server Version
  - Reader
  - Current Item
  - Current Item Kind
  - Page
  - Page Count
  - Progress Percent
  - Zoom
  - Display Mode
  - Background
  - Background Brightness State
- Registers explicit services such as `guidevault.next_page`, `guidevault.toggle_fullscreen`, `guidevault.close_reader`, and `guidevault.set_background_brightness` so controls remain usable even if HA's entity registry hides a platform after an update.
- Removes packaged `__pycache__` files.
- Uses platform string names for broader Home Assistant compatibility.

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

## Important

The installed background dropdown needs GuideVault 0.9.215 or newer so `/api/home-assistant/status` returns `availableBackgrounds`.

After installing this update, restart Home Assistant. If old entity registry rows are stale, reload the GuideVault integration once from Settings > Devices & services.
