# GuideVault Home Assistant Integration v0.5.5

This custom integration reads GuideVault's `/api/home-assistant/status` endpoint and queues reader commands through `/api/home-assistant/command`.

## New in v0.5.5

- Adds a **Toggle Fullscreen** button entity that sends `toggle_fullscreen`.
- Adds a **Reader Background** select entity populated from GuideVault's installed server-side background catalog.
- Adds **Next Background** and **Previous Background** button entities.
- Adds a **Background Brightness** number entity.
- Adds sensors/attributes for current background, available backgrounds, and fullscreen state.

## Install

Copy `custom_components/guidevault` into your Home Assistant `custom_components` directory, restart Home Assistant, then add the integration from Settings > Devices & services.

Configure:

- GuideVault URL, for example `http://192.168.1.10:5478`
- GuideVault command token from GuideVault Settings > Server > Integrations > Home Assistant

## Important

The installed background dropdown needs GuideVault 0.9.215 or newer so `/api/home-assistant/status` returns `availableBackgrounds`.
