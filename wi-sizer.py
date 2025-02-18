# -*- coding: utf-8 -*-

import streamlit as st
import math
from PIL import Image

# Import scenarios, APs, and switches data modules
from data.scenarios import SCENARIOS, get_scenario
from data.ap_models import AP_MODELS
from data.switch_models import SWITCH_MODELS

# Global Styling Constants
GLOBAL_BG_COLOR = "#F4F4F4"         # Background card color
GLOBAL_TEXT_COLOR = "#27AE60"       # Green color

# Page Layout & Container Width
st.set_page_config(
    page_title="Meraki Wi-Sizer Tool",
    page_icon="images/meraki.png",
    layout="wide"  # Use the full browser width
)

# Override container and button styling for wider layout, green buttons, etc.
st.markdown(
    """
    <style>
    /* Increase central container width */
    .block-container {
        max-width: 1400px !important;
        padding-top: 1rem;
        padding-bottom: 1rem;
        margin: auto;
    }
    /* Style all buttons (including the Calculate button) in green */
    div.stButton > button {
        background-color: #27AE60 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
    /* Custom link styling */
    a.custom-link {
        color: #27AE60;
        font-weight: bold;
        text-decoration: none;
    }
    a.custom-link:hover {
        text-decoration: underline;
    }
    /* Fix Meraki logo: remove rounding, prevent clipping, align left */
    img[src*="meraki_logo.png"] {
        border-radius: 0 !important;
        object-fit: contain !important;
        object-position: left !important;
        clip-path: none !important;
    }
    /* Reduce vertical margins for title and subtitle */
    h1 {
        margin-top: 10px !important;
        margin-bottom: 5px !important;
    }
    h2, h3, p {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Helper Functions
def calculate_aps(area: float, users: int, scenario_type: str, wifi_generation: str, ceiling_height: float = 3.0):
    concurrency = 0.7
    concurrent_users = users * concurrency
    background_per_user = concurrent_users * 2

    throughput_per_user = 4
    background_sync = 0.5

    scenario_data = get_scenario(scenario_type)
    coverage_per_ap = scenario_data["coverage_m2"]
    max_users_per_ap = scenario_data["max_users_per_ap"] #########################################################

    background_devices = 0 if scenario_type == "auditorium" else background_per_user
    devices_5ghz = math.ceil((concurrent_users + background_devices) * 0.7)
    total_bandwidth = math.ceil((concurrent_users * throughput_per_user) + (background_devices * background_sync))

    ap_capacity = 180 * 0.8  #########################################################

    # Calculate required AP count from capacity, coverage, and density
    aps_capacity = math.ceil(total_bandwidth / ap_capacity) #########################################################
    aps_coverage = math.ceil(area / coverage_per_ap) #########################################################
    aps_density = math.ceil(devices_5ghz / max_users_per_ap) #########################################################
    recommended_aps = max(aps_capacity, aps_coverage, aps_density)
    effective_users_per_ap = math.ceil(devices_5ghz / recommended_aps)

    # AP model selection based on Wi‑Fi generation and density
    if wifi_generation == "Wi-Fi 6":
        if recommended_aps <= 5 and scenario_type != "auditorium" and effective_users_per_ap <= 20:
            ap_model = "MR28"
        elif effective_users_per_ap > 30 or (scenario_type == "auditorium" and recommended_aps >= 3) or recommended_aps > 8:
            ap_model = "MR46" if effective_users_per_ap > 40 else "MR44"
        else:
            ap_model = "MR36"
    elif wifi_generation == "Wi-Fi 6E":
        if recommended_aps <= 5 and scenario_type != "auditorium" and effective_users_per_ap <= 20:
            ap_model = "CW9162"
        elif effective_users_per_ap > 30 or (scenario_type == "auditorium" and recommended_aps >= 3) or recommended_aps > 8:
            ap_model = "CW9166"
        else:
            ap_model = "CW9164"
    elif wifi_generation == "Wi-Fi 7":
        if recommended_aps <= 5 and scenario_type != "auditorium" and effective_users_per_ap <= 20:
            ap_model = "CW9172"
        elif effective_users_per_ap > 30 or (scenario_type == "auditorium" and recommended_aps >= 3) or recommended_aps > 8:
            ap_model = "CW9178"
        else:
            ap_model = "CW9176"

    ap_info = AP_MODELS[wifi_generation][ap_model].copy()
    users_per_ap = math.ceil(users / recommended_aps)
    bandwidth_per_ap = round(total_bandwidth / recommended_aps, 0)
    data_wire = math.ceil(bandwidth_per_ap * 1.5) #########################################################

    return recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info

def get_effective_port_count(switch_info: dict, required_speed: float) -> int:
    # Determine how many physical ports on the switch support at least the required speed.

    effective_count = 0
    # Get the list from the "Port Speed" key (default to an empty list if not found)
    speeds_field = switch_info.get("Port Speed", [])
    # Iterate over each port group dictionary
    for group in speeds_field:
        group_speeds = group.get("Speed (Gbps)", [])
        if group_speeds and max(group_speeds) >= required_speed:
            effective_count += group.get("Ports", 0)
    return effective_count

def calculate_switches(num_aps: int, ap_info: dict):
    # Determine the most suitable PoE switch model and how many units are needed.

    import math
    ap_power = ap_info.get("PoE")
    if not ap_power:
        st.warning("AP model doesn't have a valid PoE value.")
        return (None, None)

    port_speed = ap_info.get("Port Speed", [])
    required_speed = max(port_speed) if (isinstance(port_speed, list) and port_speed and # Add AP Uplink speed calculation
                                          all(isinstance(s, (int, float)) for s in port_speed)) else 1

    best_option = None
    best_switches_needed = None
    margin = 0.7  # 30% of margin - future growth

    for family, switches in SWITCH_MODELS.items():
        for model, info in switches.items():
            effective_port_count = get_effective_port_count(info, required_speed)
            if effective_port_count <= 0:
                continue

            effective_port_count_margin = math.floor(effective_port_count * margin)
            poe_budget = info.get("PoE Budget (W)", 0)
            poe_budget_margin = poe_budget * margin
            poe_limit_margin = math.floor(poe_budget_margin / ap_power)
            available_ports = min(effective_port_count_margin, poe_limit_margin)
            if available_ports <= 0:
                continue

            switches_needed = math.ceil(num_aps / available_ports)
            if best_option is None or (best_switches_needed is not None and switches_needed < best_switches_needed):
                best_option = (family, model, info)
                best_switches_needed = switches_needed

    return (best_option, best_switches_needed)

def format_port_config(switch_info: dict) -> str:
    # Format the switch's access port configuration details, appending " Gbps"

    port_speed_groups = switch_info.get("Port Speed", [])
    group_strings = []
    for group in port_speed_groups:
        ports = group.get("Ports")
        speeds = group.get("Speed (Gbps)", [])
        if ports is not None and speeds:
            speeds_str = "/".join(str(s) for s in speeds)
            group_strings.append(f"{ports} x {speeds_str} Gbps")
    return " + ".join(group_strings)

def render_result_card(title: str, content_html: str, bg_color: str = GLOBAL_BG_COLOR):
    # Renders a card-like container with a title and some HTML content.

    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; margin-top: 20px;">
        <h2 style="color: {GLOBAL_TEXT_COLOR}; text-align: center;">{title}</h2>
        {content_html}
    </div>
    """, unsafe_allow_html=True)

# AP & Switch Rendering Functions
def render_ap_details(ap_info: dict, ap_model: str):
    # Render the AP details section 

    # Determine number of ports (default to 1)
    ports = ap_info.get("Ports", 1)
    
    # Build a string for port speed as a single line (always include the port count)
    port_speed_list = [str(speed) for speed in ap_info.get('Port Speed', []) if isinstance(speed, (int, float))]
    speeds_str = "/".join(port_speed_list)
    port_speeds_text = f"{ports} x {speeds_str} Gbps" if speeds_str else "N/A"
    
    # Define table styles with a 30/70 column split
    table_style = "width: 100%; border-collapse: collapse; border: none;"
    first_col_style = "width: 30%; padding: 10px; text-align: left;"
    second_col_style = "width: 70%; padding: 10px; text-align: left; border-left: 1px solid #ccc;"
    bold_first_col_style = "font-weight: bold; " + first_col_style

    ap_table = f"""
    <table style="{table_style}">
      <tr>
        <td style="{bold_first_col_style}">Antenna Type:</td>
        <td style="{second_col_style}">Omnidirectional Indoor Antenna</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">Wi-Fi Standard:</td>
        <td style="{second_col_style}">{ap_info.get('Wi-Fi Standard')}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">Spatial Streams:</td>
        <td style="{second_col_style}">{ap_info.get('Spatial Streams')}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">PoE Type:</td>
        <td style="{second_col_style}">{ap_info.get('PoE Type')}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">Port Speed:</td>
        <td style="{second_col_style}">{port_speeds_text}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">SKU:</td>
        <td style="{second_col_style}">{ap_info.get('SKU')}</td>
      </tr>
    </table>
    <div style="text-align: center; margin-top: 20px;">
        <a href="{ap_info.get('Datasheet')}" target="_blank" 
           style="background-color: #27AE60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
           Datasheet
        </a>
        <a href="{ap_info.get('Installation Guide')}" target="_blank" 
           style="background-color: #27AE60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
           Installation Guide
        </a>
    </div>
    """
    # Underline the AP model in the title
    render_result_card(f"Recommended AP Model: <u>{ap_model}</u>", ap_table)

def render_switch_details(switch_option, switches_needed):
    if not switch_option:
        st.warning("No suitable switch option could be determined with the current parameters.")
        return

    family, switch_model, switch_info = switch_option
    port_config = format_port_config(switch_info)
    
    uplink_ports = switch_info.get("Uplink Ports")
    uplink_speed = switch_info.get("Uplink Speed (Gbps)")
    if isinstance(uplink_speed, list) and uplink_speed:
        uplink_speed_str = "/".join(str(s) for s in uplink_speed)
    else:
        uplink_speed_str = str(uplink_speed)
    uplink_info = f"{uplink_ports} x {uplink_speed_str} Gbps" if uplink_ports and uplink_speed else "N/A"

    unit_str = "unit" if switches_needed == 1 else "units"

    table_style = "width: 100%; border-collapse: collapse; border: none;"
    first_col_style = "width: 30%; padding: 10px; text-align: left;"
    second_col_style = "width: 70%; padding: 10px; text-align: left; border-left: 1px solid #ccc;"
    bold_first_col_style = "font-weight: bold; " + first_col_style

    # "details" block with 10px bottom margin
    details = f"""
    <div style="margin-bottom: 20px;">
      <p style="font-size: 20px; text-align: center;">
        Based on your AP requirements, you will need <strong>{switches_needed}</strong> {unit_str}.
      </p>
    </div>
    """

    # switch_table block
    switch_table = f"""
    <table style="{table_style}">
      <tr>
        <td style="{bold_first_col_style}">Access Ports:</td>
        <td style="{second_col_style}">{port_config}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">PoE Budget:</td>
        <td style="{second_col_style}">{switch_info.get('PoE Budget (W)', 0)} W</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">PoE Type:</td>
        <td style="{second_col_style}">{switch_info.get('PoE Type')}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">Uplinks:</td>
        <td style="{second_col_style}">{uplink_info}</td>
      </tr>
      <tr>
        <td style="{bold_first_col_style}">SKU:</td>
        <td style="{second_col_style}">{switch_info.get('SKU')}</td>
      </tr>
    </table>
    <div style="text-align: center; margin-top: 20px;">
        <a href="{switch_info.get('Datasheet')}" target="_blank" 
           style="background-color: #27AE60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
           Datasheet
        </a>
        <a href="{switch_info.get('Installation Guide')}" target="_blank" 
           style="background-color: #27AE60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
           Installation Guide
        </a>
    </div>
    """

    # Combine details + switch_table
    content = details + switch_table

    # Render the card with combined content
    render_result_card(f"Recommended Access Switch: <u>{switch_model}</u>", content)

def render_bom(recommended_aps, ap_info, switch_option, switches_needed):
    # Render the final Bill of Materials section.

    bom_ap_sku = ap_info.get("SKU", "N/A")
    bom_switch_sku = switch_option[2].get("SKU") if switch_option else "N/A"
    bom_switch_qty = switches_needed if switch_option else 0
    bom_html = f"""
    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <tr style="text-align: center;">
            <th style="padding: 10px;">Item</th>
            <th style="padding: 10px; border-left: 1px solid #ccc;">Quantity</th>
            <th style="padding: 10px; border-left: 1px solid #ccc;">Part Number</th>
        </tr>
        <tr style="text-align: center;">
            <td style="padding: 10px;">Access Point</td>
            <td style="padding: 10px; border-left: 1px solid #ccc;">{recommended_aps}</td>
            <td style="padding: 10px; border-left: 1px solid #ccc;">{bom_ap_sku}</td>
        </tr>
        <tr style="text-align: center;">
            <td style="padding: 10px;">PoE Access Switch</td>
            <td style="padding: 10px; border-left: 1px solid #ccc;">{bom_switch_qty}</td>
            <td style="padding: 10px; border-left: 1px solid #ccc;">{bom_switch_sku}</td>
        </tr>
    </table>
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://www.merakisizing.com/" target="_blank" 
           style="background-color: #27AE60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
           Licensing Info
        </a>
    </div>
    """
    render_result_card("Bill of Materials (BoM)", bom_html)

# Main Application
def main():
    # Display the Meraki logo in the sidebar so it's always visible
    st.sidebar.image("images/meraki_logo.png", width=150)
    
    st.title("Meraki Wi-Sizer Tool")
    st.write("Estimate the number of Access Points (APs) and PoE Switches needed for your Meraki wireless network in an indoor office environment.")

    # Sidebar Input Parameters
    st.sidebar.header("Input Parameters:")
    users = st.sidebar.number_input("Total Number of Users", min_value=1, step=5, value=50)
    area = st.sidebar.number_input("Estimated Area (m²)", min_value=20, step=10, value=100)
    ceiling_height = st.sidebar.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, step=0.1, value=3.0, format="%.1f")
    wifi_generation = st.sidebar.selectbox("Select the Wi-Fi Generation:", ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"])
    st.sidebar.checkbox("Include PoE Access Switches", value=True, key="include_switches")

    # Scenario selection
    st.subheader("Select the most compatible scenario:")
    cols = st.columns(len(SCENARIOS))
    for col, (scenario, data) in zip(cols, SCENARIOS.items()):
        with col:
            try:
                st.image(data["img"], use_container_width=True)
            except Exception:
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
        if area <= 0:
            st.warning("Please enter a valid area value.")
        elif users <= 0:
            st.warning("Please enter a valid number of users.")
        else:
            # AP Calculation
            recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info = calculate_aps(
                area=area,
                users=users,
                scenario_type=scenario_type,
                wifi_generation=wifi_generation,
                ceiling_height=ceiling_height
            )
            
            data_wire = math.ceil(bandwidth_per_ap * 1.5)
            
            # AP Summary
            ap_summary = f"""
            <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                <div style="text-align: center;">
                    <h3 style="color: {GLOBAL_TEXT_COLOR};">🏢 Quantity</h3>
                    <p style="font-size: 24px; font-weight: bold;">{recommended_aps} AP{'s' if recommended_aps != 1 else ''}</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="color: {GLOBAL_TEXT_COLOR};">👥 Density</h3>
                    <p style="font-size: 24px; font-weight: bold;">{users_per_ap} Users/AP</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="color: {GLOBAL_TEXT_COLOR};">📡 Capacity</h3>
                    <p style="font-size: 24px; font-weight: bold;">{round(data_wire)} Mbps/AP</p>
                </div>
            </div>
            """
            render_result_card("Wireless Sizing Results", ap_summary.strip())
            render_ap_details(ap_info, ap_model)

            # PoE Access Switch Calculation & Display
            if st.session_state.include_switches:
                switch_option, switches_needed = calculate_switches(recommended_aps, ap_info)
                render_switch_details(switch_option, switches_needed)
            else:
                switch_option = None
                switches_needed = None

            # BoM
            render_bom(recommended_aps, ap_info, switch_option, switches_needed)

            # Disclaimer Section
            if (area > 1200 or ceiling_height > 4.5 or users > 500 or recommended_aps > 12 or (scenario_type == "auditorium" and recommended_aps >= 5)):
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
                    "<p>This tool provides a preliminary estimation and doesn't replace a full Predictive Site Survey.</p>"
                    "</div>",
                    unsafe_allow_html=True
                )

    # Footer
    st.markdown(
        """
        <hr>
        <div style="text-align: center; font-size: 0.8rem; color: #555; margin-top: 20px;">
            Designed by Caio Scarpa | Last Updated 02/06/2025
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
