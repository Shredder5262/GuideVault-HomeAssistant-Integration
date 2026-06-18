# GuideVault Home Assistant Integration v0.5.9

This custom integration reads GuideVault's `/api/home-assistant/status` endpoint and queues reader commands through `/api/home-assistant/command`.

## Fixed in v0.5.9

- Restores the clean setup wizard from the working build: only **GuideVault URL** and **GuideVault command token**.
- Removes the optional control/background enable flags that could accidentally hide controls.
- Always loads the full GuideVault control surface:
  - First/Previous/Next/Last page
  - Toggle Overlay
  - Toggle Fullscreen
  - Fullscreen switch and sensor
  - Close Reader
  - Zoom In/Out and Zoom slider
  - Page number control
  - Display Mode selector
  - Reader Background selector populated by GuideVault
  - Next/Previous Background
  - Background Brightness slider
  - Version and reader status sensors
- Keeps fallback services such as `guidevault.next_page`, `guidevault.toggle_fullscreen`, `guidevault.close_reader`, and `guidevault.set_background_brightness`.
- Keeps diagnostics out of the package to avoid stale diagnostics import warnings after failed overlays.

## Clean update recommendation

If a previous v0.5.7/v0.5.8 install hid entities or left stale files behind:

1. Stop Home Assistant.
2. Delete `/config/custom_components/guidevault`.
3. Copy this package's `custom_components/guidevault` folder into `/config/custom_components/guidevault`, or reinstall through HACS.
4. Start Home Assistant.
5. Remove and re-add the GuideVault integration if the old config entry still does not show controls.

## Requirement

The installed background dropdown needs GuideVault 0.9.215 or newer so `/api/home-assistant/status` returns `availableBackgrounds`.
