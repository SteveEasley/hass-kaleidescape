# Home Assistant integration for Kaleidescape movie players

The Kaleidescape integration allows for the automation of Kaleidescape movie players in Home Assistant. Services and attributes are exposed for building advanced automations. Ideas include:

- The start of movie credits automatically turns up lights.
- Playing and pausing a movie sets lighting scenes.
- A change in aspect ratio controls a masking system.
- A change in video resolution controls a lens system or video scaler.

## Supported Models

This integration is intended for the automation of Kaleidescape players with a movie zone. These players will automatically have a respective Home Assistant media player added. Any music zone in a player is ignored at this time.

Testing was done on a Strato S with kOS `10.11.0-22557`.
