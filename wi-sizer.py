import streamlit as st
import math
from PIL import Image

# Import the modules with scenarios, AP model, and switch model
from data.scenarios import SCENARIOS, get_scenario
from data.ap_models import AP_MODELS
from data.switch_models import SWITCH_MODELS

# Function to calculate the number of APs and recommended model
def calculate_aps(area: float, users: int, scenario_type: str, ceiling_height: float = 3.0):
    # Throughput parameters
    throughput_per_user = 4
    background_sync = 0.5
    concurrency = 0.7

    # Simultaneous users
    concurrent_users = math.ceil(users * concurrency)

    # Load scenario data
    scenario_data = get_scenario(scenario_type)
    coverage_per_ap = scenario_data["coverage_m2"]
    max_users_per_ap = scenario_data["max_users_per_ap"]

    # Background devices
    if scenario_type == "auditorium":
        background_devices = 0
    else:
        background_devices = concurrent_users

    devices_5ghz = math.ceil((concurrent_users + background_devices) * 0.7)

    # Total bandwidth required
    total_bandwidth = (concurrent_users * throughput_per_user) + (background_devices * background_sync)

    # Average AP capacity 5GHz (MR28)
    ap_capacity = 180 * 0.8 # 126 Mbps

    # APs calculations
    aps_capacity = math.ceil(total_bandwidth / ap_capacity)
    aps_coverage = math.ceil(area / coverage_per_ap)
    aps_density = math.ceil(devices_5ghz / max_users_per_ap)

    # Maximum value from all calculations
    recommended_aps = max(aps_capacity, aps_coverage, aps_density)

    # AP model recommendation
    effective_users_per_ap = devices_5ghz / recommended_aps

    # Model selection logic using AP_MODELS
    if (recommended_aps <= 5 and scenario_type != "auditorium" and effective_users_per_ap <= 20):
        ap_model = "MR28"
        ap_info = AP_MODELS["Wi-Fi 6"]["MR28"].copy()
    elif (effective_users_per_ap > 30 or (scenario_type == "auditorium" and recommended_aps >= 3) or recommended_aps > 8):
        ap_model = "MR44"
        ap_info = AP_MODELS["Wi-Fi 6"]["MR44"].copy()
    else:
        ap_model = "MR36"
        ap_info = AP_MODELS["Wi-Fi 6"]["MR36"].copy()

    ap_info["Environment"] = "Indoor"

    # Users per AP and consumption per AP
    users_per_ap = math.ceil(users / recommended_aps)
    bandwidth_per_ap = round(total_bandwidth / recommended_aps, 0)

    return recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info

def main():
    st.set_page_config(
        page_title="Meraki Wi-Sizer Tool",
        page_icon="images/logo.png",
        layout="centered"
    )

    # Custom CSS (previous implementation)
    st.markdown("""
        <style>
        .block-container { max-width: 1000px; margin: auto; }
        .meraki-title { color: #67B346; font-weight: bold; text-align: center; }
        .meraki-subtitle { color: #67B346; text-align: center; }

        div.stButton > button {
            background-color: #179C7D !important;
            color: #FFF !important;
            border-radius: 8px !important;
            border: none !important;
        }

        a.custom-link {
            color: #179C7D;
            font-weight: bold;
            text-decoration: none;
        }
        a.custom-link:hover {
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.image("images/meraki_logo.png", width=150)
    st.title("Meraki Wi-Sizer Tool")
    st.write("Estimate the number of Access Points (APs) needed for your Meraki wireless network budget offer in an indoor office environment.")

    # Input Parameters
    st.sidebar.header("Input Parameters:")
    users = st.sidebar.number_input("Total Number of Users", min_value=1, step=5, value=50)
    area = st.sidebar.number_input("Estimated Area (m²)", min_value=20, step=10, value=100)
    ceiling_height = st.sidebar.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, step=0.1, value=3.0)
    wifi_generation = st.sidebar.selectbox("Select the Wi-Fi Generation:", ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"])
    include_switches = st.sidebar.checkbox("Include PoE Switches")

    # Scenario selection
    st.subheader("Select the most compatible scenario:")
    cols = st.columns(len(SCENARIOS))
    
    for col, (scenario, data) in zip(cols, SCENARIOS.items()):
        with col:
            try:
                st.image(data["img"], use_container_width=True)
            except:
                st.write("Image not found.")
            st.caption(f"**{data['name']}** {data['description']}")

    scenario_type = st.radio(
        label="Select the scenario:",
        options=list(SCENARIOS.keys()),
        format_func=lambda x: SCENARIOS[x]["name"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Calculate Button
    if st.button("Calculate"):
        # Validate inputs
        if area <= 0:
            st.warning("Please enter a valid area value.")
        elif users <= 0:
            st.warning("Please enter a valid number of users.")
        else:
            # Perform calculation
            recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info = calculate_aps(
                area=area, users=users, scenario_type=scenario_type, ceiling_height=ceiling_height
            )
            
            # Results display
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
                <h2 style='color: #179C7D; text-align: center;'>Wireless Sizing Results</h2>
                <div style='display: flex; justify-content: space-around; margin-top: 20px;'>
                    <div style='text-align: center;'>
                        <h3 style='color: #179C7D;'>🏢 Quantity</h3>
                        <p style='font-size: 24px; font-weight: bold;'>At least {} APs</p>
                    </div>
                    <div style='text-align: center;'>
                        <h3 style='color: #179C7D;'>👥 Density</h3>
                        <p style='font-size: 24px; font-weight: bold;'>{} Users/AP</p>
                    </div>
                    <div style='text-align: center;'>
                        <h3 style='color: #179C7D;'>📡 Capacity</h3>
                        <p style='font-size: 24px; font-weight: bold;'>{} Mbps/AP</p>
                    </div>
                </div>
            </div>
            """.format(recommended_aps, users_per_ap, round(bandwidth_per_ap)), unsafe_allow_html=True)

            # AP Details Card
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                <h2 style='color: #179C7D; text-align: center;'>Recommended AP Model: {}</h2>
                <div style='display: flex; justify-content: space-between; margin-top: 20px;'>
                    <div style='width: 60%;'>
                        <h3 style='color: #179C7D;'>🌐 Technical Specifications</h3>
                        <table style='width: 100%; border-collapse: separate; border-spacing: 0 10px;'>
                            <tr>
                                <td style='font-weight: bold;'>Environment:</td>
                                <td>{}</td>
                            </tr>
                            <tr>
                                <td style='font-weight: bold;'>Wi-Fi Standard:</td>
                                <td>{}</td>
                            </tr>
                            <tr>
                                <td style='font-weight: bold;'>Spatial Streams:</td>
                                <td>{}</td>
                            </tr>
                            <tr>
                                <td style='font-weight: bold;'>SKU:</td>
                                <td>{}</td>
                            </tr>
                        </table>
                    </div>
                    <div style='width: 35%;'>
                        <h3 style='color: #179C7D;'>⚡ Port Speeds</h3>
                        <div style='display: flex; flex-wrap: wrap; gap: 10px;'>
                            {}
                        </div>
                    </div>
                </div>
                <div style='text-align: center; margin-top: 20px;'>
                    <a href="{}" target="_blank" style='background-color: #179C7D; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;'>Datasheet</a>
                    <a href="{}" target="_blank" style='background-color: #179C7D; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Installation Guide</a>
                </div>
            </div>
            """.format(
                ap_model, 
                ap_info['Environment'], 
                ap_info['Wi-Fi Standard'], 
                ap_info['Spatial Streams'], 
                ap_info['SKU'],
                # Port speeds visualization
                ''.join([f'<div style="background-color: #179C7D; color: white; padding: 5px 10px; border-radius: 5px;">{speed} Gbps</div>' for speed in ap_info['Port Speed']]),
                ap_info['Datasheet'], 
                ap_info['Installation Guide']
            ), unsafe_allow_html=True)

            # Warnings
            if (area > 1200 or ceiling_height > 4.5 or users > 500 or (scenario_type == "auditorium" and recommended_aps >= 5)):
                st.markdown(
                    "<div style='text-align: center; color: red; margin-top: 20px;'>"
                    "<h4>🚨 Predictive Site Survey Recommended</h4>"
                    "<p>Given the complexity of the requirements, a Predictive Site Survey is strongly recommended. Contact your SE.</p>"
                    "</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div style='text-align: center; color: red; margin-top: 20px;'>"
                    "<h4>⚠️ Preliminary Estimation Disclaimer</h4>"
                    "<p>This tool provides a preliminary estimation, it doesn't replace a Predictive Site Survey. Use it for non-mission-critical scenarios only.</p>"
                    "</div>",
                    unsafe_allow_html=True
                )

    st.markdown(
        """
        <hr>
        <div style='text-align: center; font-size: 0.8rem; color: #555; margin-top: 20px;'>
            Designed by Caio Scarpa | Last Updated 02/06/2025
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
