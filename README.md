# Version 0.1.3
Initial Release

# hass_gira_iot_api
Home Assistant integration to connect your X1/Homeserver via REST API based on this documentation:
https://partner.gira.de/data3/Gira_IoT_REST_API_v2_DE.pdf

# hass_gira_iot_api
This integration adds the devices you have configured in your Gira X1 / Gira Homeserver to HomeAssistant.
For now only lights are supported

## Installation

### HACS (manually add Repository)

Add this repository to HACS.
* In the HACS GUI, select "Custom repositories"
* Enter the following repository URL: https://github.com/MadOne/hass_gira_iot_api
* Category: Integration
* After adding the integration, restart Home Assistant.
* Now press the button "Add Integration" in Configuration -> Integrations to install it in Home assistant.
* Now under Configuration -> Integrations, "HomeAssistant Gira IOT API" should be available.

### Manual install

Create a directory called `hass_gira_iot_api` in the `<config directory>/custom_components/` directory on your Home Assistant
instance. Install this component by copying all files in `/custom_components/hass_gira_iot_api/` folder from this repo into the
new `<config directory>/custom_components/hass_gira_iot_api/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── hass_gira_iot_api
│   ├── __init__.py
│   ├── ...
│   ├── ...
│   ├── ...
│   └── light.py
```
## Configuration
<img width="419" height="581" alt="Screenshot From 2025-10-19 20-03-50" src="https://github.com/user-attachments/assets/a9f02c36-7c37-404e-b835-71f56033a70a" />



The only mandatory parameters are:
* The IP-Address of your Gira Iot  device.
* The user name.
* The password.
* Port used for the CallBack Server. This port has to be free and accessible from your homenetwork
* Ip of the HomeAssistant. This is needed to register the CallBack url.

# Disclaimer
The developers of this integration are not affiliated with Gira. They have created the integration as open source in their spare time on the basis of publicly accessible information.
The use of the integration is at the user's own risk and responsibility. The developers are not liable for any damages arising from the use of the integration.
