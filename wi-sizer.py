import streamlit as st
import math
from PIL import Image

# Import modules containing scenarios, AP models, and switch models
from data.scenarios import SCENARIOS, get_scenario
from data.ap_models import AP_MODELS
from data.switch_models import SWITCH_MODELS

# ---------------------------
# Global Styling Constants
# ---------------------------
GLOBAL_BG_COLOR = "#f0f2f6"
GLOBAL_TEXT_COLOR = "#179C7D"
BUTTON_BG_COLOR = "#179C7D"

# ---------------------------
# Helper Functions
# ---------------------------
def calculate_aps(area: float, users: int, scenario_type: str, wifi_generation: str, ceiling_height: float = 3.0):
    """
    Calculate the recommended number of APs, select the appropriate AP model,
    and compute per-AP metrics.
    
    Returns:
        recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info
    """
    throughput_per_user = 4
    background_sync = 0.5
    concurrency = 0.7
    concurrent_users = math.ceil(users * concurrency)

    scenario_data = get_scenario(scenario_type)
    coverage_per_ap = scenario_data["coverage_m2"]
    max_users_per_ap = scenario_data["max_users_per_ap"]

    background_devices = 0 if scenario_type == "auditorium" else math.ceil(concurrent_users * 1.5)
    devices_5ghz = math.ceil((concurrent_users + background_devices) * 0.7)
    total_bandwidth = (concurrent_users * throughput_per_user) + (background_devices * background_sync)

    # Use a baseline capacity (e.g., MR28 baseline: 180 * 0.8 = 126 Mbps)
    ap_capacity = 180 * 0.8  

    # Calculate AP count from capacity, coverage, and density
    aps_capacity = math.ceil(total_bandwidth / ap_capacity)
    aps_coverage = math.ceil(area / coverage_per_ap)
    aps_density = math.ceil(devices_5ghz / max_users_per_ap)
    recommended_aps = max(aps_capacity, aps_coverage, aps_density)
    effective_users_per_ap = devices_5ghz / recommended_aps

    # AP model selection logic based on Wi‑Fi generation and density
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
    else:
        ap_model = "MR28"  # Fallback

    ap_info = AP_MODELS[wifi_generation][ap_model].copy()
    ap_info["Environment"] = "Indoor"
    users_per_ap = math.ceil(users / recommended_aps)
    bandwidth_per_ap = round(total_bandwidth / recommended_aps, 0)
    data_wire = math.ceil(bandwidth_per_ap * 1.5)

    return recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info

def get_effective_port_count(switch_info: dict, required_speed: float) -> int:
    """
    Determine how many physical ports on the switch support at least the required speed.
    Works for both grouped definitions (list of dicts) and simple lists.
    """
    if "Port Speed" in switch_info:
        speeds_field = switch_info["Port Speed"]
        if isinstance(speeds_field, list) and all(isinstance(item, dict) for item in speeds_field):
            effective_count = 0
            for group in speeds_field:
                group_speeds = group.get("Speed (Gbps)", [])
                if group_speeds and max(group_speeds) >= required_speed:
                    effective_count += group.get("Ports", 0)
            return effective_count
        elif isinstance(speeds_field, list):
            return sum(1 for speed in speeds_field if speed >= required_speed)
    elif "Port Speed (Gbps)" in switch_info:
        speeds = switch_info["Port Speed (Gbps)"]
        if isinstance(speeds, list):
            if len(speeds) == 1 and switch_info.get("Access Ports"):
                return switch_info["Access Ports"] if speeds[0] >= required_speed else 0
            else:
                return sum(1 for speed in speeds if speed >= required_speed)
    return 0

def calculate_switches(num_aps: int, ap_info: dict):
    """
    Determine the most suitable PoE switch model and how many units are needed based on:
      - Number of APs,
      - AP PoE draw,
      - Available switch ports (that support the required speed),
      - And the switch's PoE budget.
      
    A 30% margin is applied to both the switch's port count and PoE budget.
    
    Returns:
        best_option (tuple: (family, model, switch_info)) and switches_needed.
        Returns (None, None) if no suitable switch is found.
    """
    import math
    ap_power = ap_info.get("POE") or ap_info.get("PoE")
    if not ap_power:
        st.warning("AP model does not have a valid PoE value.")
        return (None, None)

    port_speed = ap_info.get("Port Speed", [])
    required_speed = max(port_speed) if (isinstance(port_speed, list) and port_speed and 
                                          all(isinstance(s, (int, float)) for s in port_speed)) else 1

    best_option = None
    best_switches_needed = None

    # Define margin factor: only 70% of capacity is considered.
    margin = 0.7

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
    """
    Format the switch's access port configuration details.
    For a grouped port configuration, return a string like:
      "8 x 1/2.5/5/10G + 16 x 1G"
    If a simple list is provided, then display it as:
      "X x YG" (e.g., "4 x 10G").
    """
    if "Port Speed" in switch_info:
        speeds_field = switch_info["Port Speed"]
        if isinstance(speeds_field, list) and all(isinstance(item, dict) for item in speeds_field):
            group_strings = []
            for group in speeds_field:
                ports = group.get("Ports")
                speeds = group.get("Speed (Gbps)", [])
                if ports is not None and speeds:
                    speeds_str = "/".join(str(s) for s in speeds)
                    group_strings.append(f"{ports} x {speeds_str}G")
            return " + ".join(group_strings)
        elif isinstance(speeds_field, list):
            access_ports = switch_info.get("Access Ports")
            if access_ports is not None and speeds_field:
                speeds_str = "/".join(str(s) for s in speeds_field)
                return f"{access_ports} x {speeds_str}G"
    elif "Port Speed (Gbps)" in switch_info:
        speeds = switch_info["Port Speed (Gbps)"]
        access_ports = switch_info.get("Access Ports")
        if access_ports is not None and isinstance(speeds, list) and speeds:
            if len(speeds) == 1:
                return f"{access_ports} x {speeds[0]}G"
            else:
                speeds_str = "/".join(str(s) for s in speeds)
                return f"{access_ports} x {speeds_str}G"
    return ""

def render_result_card(title: str, content_html: str, bg_color: str = GLOBAL_BG_COLOR):
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; margin-top: 20px;">
        <h2 style="color: {GLOBAL_TEXT_COLOR}; text-align: center;">{title}</h2>
        {content_html}
    </div>
    """, unsafe_allow_html=True)

def render_ap_details(ap_info: dict, ap_model: str):
    """
    Render the AP details section.
    """
    port_speeds = ''.join(
        [f'<div style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 5px 10px; border-radius: 5px; margin: 2px;">{speed} Gbps</div>'
         for speed in ap_info.get('Port Speed', []) if isinstance(speed, (int, float))]
    )
    details = f"""
    <div style="display: flex; justify-content: space-between; margin-top: 20px;">
        <div style="width: 60%;">
            <h3 style="color: {GLOBAL_TEXT_COLOR};">🌐 Technical Specifications</h3>
            <table style="width: 100%; border-collapse: separate; border-spacing: 0 10px;">
                <tr>
                    <td style="font-weight: bold;">Environment:</td>
                    <td>{ap_info.get('Environment')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Wi-Fi Standard:</td>
                    <td>{ap_info.get('Wi-Fi Standard')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Spatial Streams:</td>
                    <td>{ap_info.get('Spatial Streams')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">PoE Type:</td>
                    <td>{ap_info.get('PoE Type')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">SKU:</td>
                    <td>{ap_info.get('SKU')}</td>
                </tr>
            </table>
        </div>
        <div style="width: 35%;">
            <h3 style="color: {GLOBAL_TEXT_COLOR};">⚡ Port Speeds</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                {port_speeds}
            </div>
        </div>
    </div>
    <div style="text-align: center; margin-top: 20px;">
        <a href="{ap_info.get('Datasheet')}" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">Datasheet</a>
        <a href="{ap_info.get('Installation Guide')}" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Installation Guide</a>
    </div>
    """
    render_result_card(f"Recommended AP Model: {ap_model}", details)

def render_switch_details(switch_option, switches_needed):
    """
    Render the PoE switch details section.
    """
    if not switch_option:
        st.warning("No suitable PoE switch option could be determined with the current parameters.")
        return

    family, switch_model, switch_info = switch_option

    # Format the access port configuration using format_port_config()
    port_config = format_port_config(switch_info)

    # Combine uplink information into a single row.
    uplink_ports = switch_info.get("Uplink Ports")
    uplink_speed = switch_info.get("Uplink Speed (Gbps)")
    if isinstance(uplink_speed, list) and uplink_speed:
        uplink_speed_str = "/".join(str(s) for s in uplink_speed)
    else:
        uplink_speed_str = str(uplink_speed)
    uplink_info = f"{uplink_ports} x {uplink_speed_str}G" if uplink_ports and uplink_speed else "N/A"

    details = f"""
    <div style="text-align: center;">
        <p style="font-size: 20px;">Based on your AP requirements, you will need <strong>{switches_needed}</strong> unit(s) of:</p>
        <h3 style="color: {GLOBAL_TEXT_COLOR};">{switch_model} ({family})</h3>
    </div>
    <div style="margin-top: 20px;">
        <table style="width: 100%; border-collapse: separate; border-spacing: 0 10px;">
            <tr>
                <td style="font-weight: bold;">Access Ports:</td>
                <td>{port_config}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">PoE Budget (W):</td>
                <td>{switch_info.get('PoE Budget (W)')}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">PoE Type:</td>
                <td>{switch_info.get('PoE Type')}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Uplink:</td>
                <td>{uplink_info}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">SKU:</td>
                <td>{switch_info.get('SKU')}</td>
            </tr>
        </table>
    </div>
    <div style="text-align: center; margin-top: 20px;">
        <a href="{switch_info.get('Datasheet')}" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">Datasheet</a>
        <a href="{switch_info.get('Installation Guide')}" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Installation Guide</a>
    </div>
    """
    render_result_card("Recommended PoE Switch Solution", details)

def render_bom(recommended_aps, ap_info, switch_option, switches_needed):
    """
    Render the final Bill of Materials section.
    """
    bom_ap_sku = ap_info.get("SKU", "N/A")
    bom_switch_sku = switch_option[2].get("SKU") if switch_option else "N/A"
    bom_switch_qty = switches_needed if switch_option else 0
    bom_html = f"""
    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <tr style="background-color: {GLOBAL_BG_COLOR};">
            <th style="padding: 10px; text-align: left;">Item</th>
            <th style="padding: 10px; text-align: left;">Quantity</th>
            <th style="padding: 10px; text-align: left;">Part Number</th>
        </tr>
        <tr>
            <td style="padding: 10px;">Access Points</td>
            <td style="padding: 10px;">{recommended_aps}</td>
            <td style="padding: 10px;">{bom_ap_sku}</td>
        </tr>
        <tr>
            <td style="padding: 10px;">PoE Switches</td>
            <td style="padding: 10px;">{bom_switch_qty}</td>
            <td style="padding: 10px;">{bom_switch_sku}</td>
        </tr>
    </table>
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://www.merakisizing.com/" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Licensing Info</a>
    </div>
    """
    render_result_card("Bill of Materials (BoM)", bom_html)

# ---------------------------
# Main Application
# ---------------------------
def main():
    st.set_page_config(
        page_title="Meraki Wi-Sizer Tool",
        page_icon="images/meraki.png",
        layout="centered"
    )

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
            font-weight: bold !important;
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

    st.image("images/meraki_logo.png", width=150)
    st.title("Meraki Wi-Sizer Tool")
    st.write("Estimate the number of Access Points (APs) and PoE Switches needed for your Meraki wireless network in an indoor environment.")

    # Sidebar Input Parameters
    st.sidebar.header("Input Parameters:")
    users = st.sidebar.number_input("Total Number of Users", min_value=1, step=5, value=50)
    area = st.sidebar.number_input("Estimated Area (m²)", min_value=20, step=10, value=100)
    ceiling_height = st.sidebar.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, step=0.1, value=3.0)
    wifi_generation = st.sidebar.selectbox("Select the Wi-Fi Generation:", ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"])
    include_switches = st.sidebar.checkbox("Include PoE Switches", value=True)

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

    # Calculation trigger
    if st.button("Calculate"):
        if area <= 0:
            st.warning("Please enter a valid area value.")
        elif users <= 0:
            st.warning("Please enter a valid number of users.")
        else:
            recommended_aps, ap_model, users_per_ap, bandwidth_per_ap, ap_info = calculate_aps(
                area=area,
                users=users,
                scenario_type=scenario_type,
                wifi_generation=wifi_generation,
                ceiling_height=ceiling_height
            )
            
            # AP Summary Section – ensure the HTML is stripped of extra whitespace
            ap_summary = f"""<div style="display: flex; justify-content: space-around; margin-top: 20px;">
    <div style="text-align: center;">
        <h3 style="color: {GLOBAL_TEXT_COLOR};">🏢 Quantity</h3>
        <p style="font-size: 24px; font-weight: bold;">{recommended_aps} APs</p>
    </div>
    <div style="text-align: center;">
        <h3 style="color: {GLOBAL_TEXT_COLOR};">👥 Density</h3>
        <p style="font-size: 24px; font-weight: bold;">{users_per_ap} Users/AP</p>
    </div>
    <div style="text-align: center;">
        <h3 style="color: {GLOBAL_TEXT_COLOR};">📡 Capacity</h3>
        <p style="font-size: 24px; font-weight: bold;">{round(data_wire)} Mbps/AP</p>
    </div>
</div>""".strip()
            render_result_card("Wireless Sizing Results", ap_summary)
            render_ap_details(ap_info, ap_model)

            # PoE Switch Section (if selected)
            if include_switches:
                switch_option, switches_needed = calculate_switches(recommended_aps, ap_info)
                render_switch_details(switch_option, switches_needed)
            else:
                switch_option = None
                switches_needed = None

            # Final BoM Section
            render_bom(recommended_aps, ap_info, switch_option, switches_needed)

            # Disclaimer Section
            if (area > 1200 or ceiling_height > 4.5 or users > 500 or 
                (scenario_type == "auditorium" and recommended_aps >= 5)):
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
                    "<p>This tool provides a preliminary estimation and does not replace a full Predictive Site Survey.</p>"
                    "</div>",
                    unsafe_allow_html=True
                )

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
