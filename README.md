# Meraki Wi-Sizer Tool

## Overview
The Meraki Wi-Sizer Tool is a web-based application built with Streamlit to **estimate the required number of Meraki Access Points (APs) for a given indoor office environment**. This tool provides a preliminary wireless sizing estimation based on area, user density, and predefined scenarios, helping users make data-driven decisions about their Meraki wireless deployments.

## Features
- **Scenario-Based AP Estimation** – Choose from predefined office layouts to determine the number of APs required.
- **Wi-Fi Generation Selection** – Supports Wi-Fi 6, Wi-Fi 6E, and Wi-Fi 7 for accurate model recommendations.
- **AP Model Recommendations** – Suggests the best Meraki AP model based on user density and bandwidth needs.
- **PoE Switch Integration** – Optionally recommends PoE switches to power APs based on power and bandwidth requirements.
- **Detailed AP & Switch Specifications** – Retrieves relevant device details from structured JSON-based data files.
- **Streamlit Web UI** – Simple and interactive interface for seamless wireless network sizing.

## Technologies Used
- **Python 3**
- **Streamlit** (for the UI)
- **Pandas** (for data handling)
- **JSON** (for storing details)

## How to Use
1. Select the relevant input parameters:
   - Number of users
   - Estimated area (m²)
   - Ceiling height (m)
   - Scenario selection (Office 1, Office 2, Office 3, Auditorium)
   - Wi-Fi generation (Wi-Fi 6, Wi-Fi 6E, Wi-Fi 7)
   - Option to include PoE switches
2. Click **Calculate** to get AP and switch recommendations.

## Project Structure
```
wi-sizer/
│── images/
│── data/
│   ├── scenarios.py
│   ├── ap_models.py
│   ├── switch_models.py
│── wi-sizer.py           
│── requirements.txt    
│── README.md        
```

## References
This project was developed based on several key references and best practices:
- [Meraki Wireless for Enterprise Best Practices- RF Design](https://documentation.meraki.com/Architectures_and_Best_Practices/Meraki_Wireless_for_Enterprise_Best_Practices/Meraki_Wireless_for_Enterprise_Best_Practices-_RF_Design)

[Meraki Documentation](https://documentation.meraki.com/) 🚀

## License
This project is licensed under the MIT License.

## Disclaimer
This tool provides a **preliminary estimation** and **does not replace a professional predictive site survey**. It should be used only for initial sizing and budgetary purposes.

## Author
Developed by **Caio Scarpa**
