# Meraki Wi-Sizer Tool

## Overview
The **Meraki Wi-Sizer Tool** is a web application built with **Streamlit** to estimate the number of Meraki Access Points (APs) needed for a given indoor office environment. The tool provides a preliminary wireless sizing estimation based on area, user count, and predefined scenarios, helping users make informed decisions about Meraki wireless solutions.

## Features
- **Scenario-based AP estimation:** Select from predefined office environments to calculate the required number of APs.
- **Wi-Fi Generation Selection:** Choose between **Wi-Fi 6, Wi-Fi 6E, and Wi-Fi 7** for accurate model recommendations.
- **Access Point Model Selection:** Determines the best AP model based on user density and bandwidth needs.
- **PoE Switch Integration:** Option to include **PoE switch recommendations** based on AP power and bandwidth requirements.
- **Detailed AP & Switch Specifications:** Retrieves relevant AP and switch details from separate JSON data files.

## Technologies Used
- **Python 3**
- **Streamlit** (for the UI)
- **Pandas** (for data handling)
- **JSON** (for storing AP and switch model details)

## Installation
### Prerequisites
Make sure you have the following installed:
- **Python 3.8+**
- **pip** (Python package manager)

### Setup Instructions
1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/meraki-wi-sizer.git
   cd meraki-wi-sizer
   ```
2. **Create a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. **Run the application:**
   ```sh
   streamlit run wi-sizer.py
   ```
2. Open the provided **localhost link** in your browser.
3. Select the relevant input parameters:
   - Number of users
   - Estimated area (m²)
   - Ceiling height (m)
   - Scenario selection (Office 1, Office 2, Office 3, Auditorium)
   - Wi-Fi generation (Wi-Fi 6, Wi-Fi 6E, Wi-Fi 7)
   - Option to include PoE switches
4. Click **Calculate** to get AP and switch recommendations.

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
