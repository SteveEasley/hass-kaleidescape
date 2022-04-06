# Home Assistant integration for Kaleidescape movie players

This integration is now officially part of [HomeAssistant](https://www.home-assistant.io/)! Please refer to https://www.home-assistant.io/integrations/kaleidescape for details.

## Upgrading to the official version

If you were using this version, be sure to remove it before using upgrading to HomeAssistant 2022.4. Your existing automations and scripts should be fine, but will likely require some naming edits to match the changes in the official version. 

- The naming format for entities was changed. For instance if you have a player with the name `Theater`, the new entity name in HomeAssistant will be `media_player.kaleidescape_theater`. The old name would have been `media_player.theater_kaleidescape`, which you will need to change in your automations and scripts.
- Many of the previous media_player attributes are were split out into separate Sensor entities. If you were using them, see https://www.home-assistant.io/integrations/kaleidescape#sensor.
