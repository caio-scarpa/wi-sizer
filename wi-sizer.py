# -*- coding: utf-8 -*-

import streamlit as st
import math
import os
import json
import openai  # or your pinned openai version
from PIL import Image

# Import scenarios, APs, and switches data modules
from data.scenarios import SCENARIOS, get_scenario
from data.ap_models import AP_MODELS
from data.switch_models import SWITCH_MODELS

# Global Styling Constants
GLOBAL_BG_COLOR = "#F4F4F4"
GLOBAL_TEXT_COLOR = "#27AE60"

# Page Layout & Container Width
st.set_page_config(
    page_title="Meraki Wi-Sizer Tool (beta)",
    page_icon="images/meraki.png",
    layout="wide"
)

openai.api_key = "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"

st.markdown(
    f"""
    <style>
    .block-container {{
        max-width: 1400px !important;
        padding-top: 1rem;
        padding-bottom: 1rem;
        margin: auto;
    }}
    div.stButton > button {{
        background-color: {GLOBAL_TEXT_COLOR} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }}
    a.custom-link {{
        color: {GLOBAL_TEXT_COLOR};
        font-weight: bold;
        text-decoration: none;
    }}
    a.custom-link:hover {{
        text-decoration: underline;
    }}
    img[src*="meraki_logo.png"] {{
        border-radius: 0 !important;
        object-fit: contain !important;
        object-position: left !important;
        clip-path: none !important;
    }}
    h1 {{
        margin-top: 10px !important;
        margin-bottom: 5px !important;
    }}
    h2, h3, p {{
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# HELPER FUNCTIONS

def calculate_aps(area: float, users: int, scenario_type: str, wifi_generation: str, ceiling_height: float = 3.0):
    # Baseline calculations
    concurrency = 0.7  # 70% occupancy
    concurrent_users = users * concurrency
    background_per_user = concurrent_users * 1.5  # 1.5 devices per person
    background_devices = 0 if scenario_type == "auditorium" else background_per_user

    throughput_per_user = 4  # Mbps
    background_sync = 0.5  # Mbps

    total_bandwidth = math.ceil((concurrent_users * throughput_per_user) + (background_devices * background_sync))  # Mbps
    devices_5ghz = math.ceil((concurrent_users + background_devices) * 0.7)

    # Get scenario data (which contains coverage_m2)
    scenario_data = get_scenario(scenario_type)
    coverage_m2 = scenario_data.coverage_m2

    # 1. Coverage-based AP count
    aps_coverage = math.ceil(area / coverage_m2)
    
    # 2. Estimated users per AP based on coverage alone
    users_ap = math.ceil(concurrent_users / aps_coverage)

    # 3. Select an AP model from the specified Wi-Fi generation whose "Max Users" >= users_ap
    candidates = []
    for model, info in AP_MODELS[wifi_generation].items():
        # If aps_coverage > 5, do not consider MR28
        if aps_coverage > 5 and model == "MR28":
            continue
        max_users = info.get("Max Users", 0)
        if max_users >= users_ap:
            candidates.append((model, info, max_users))
    if not candidates:
        st.warning("The estimated users per AP exceed the capacity of available models. Using the model with the highest 'Max Users' available.")
        candidates = [(model, info, info.get("Max Users", 0)) for model, info in AP_MODELS[wifi_generation].items()
                      if not (aps_coverage > 5 and model == "MR28")]
        candidates.sort(key=lambda x: x[2], reverse=True)
        selected_candidate = candidates[0]
    else:
        candidates.sort(key=lambda x: x[2])
        selected_candidate = candidates[0]
    selected_model, selected_info, selected_max_users = selected_candidate

    # 4. Capacity-based AP count using the selected AP's capacity (5GHz + 6GHz if available)
    capacity_5ghz = selected_info.get("Capacity", {}).get("5GHz", 0)
    capacity_6ghz = selected_info.get("Capacity", {}).get("6GHz", 0)
    if capacity_6ghz > 0:
        effective_capacity = capacity_5ghz + capacity_6ghz
    else:
        effective_capacity = capacity_5ghz

    factor = 0.35  # factor to represent real-world data rate
    if effective_capacity <= 0:
        aps_capacity = float('inf')
    else:
        aps_capacity = math.ceil(total_bandwidth / (effective_capacity * factor))

    # 5. Density-based AP count based on the selected AP's "Max Users"
    aps_density = math.ceil(devices_5ghz / selected_max_users)

    # 6. Final recommendation is the maximum of coverage, capacity, and density counts
    recommended_aps = max(aps_coverage, aps_capacity, aps_density)
    
    users_per_ap = math.ceil(users / recommended_aps)
    wire_speed = math.ceil((total_bandwidth * 3) / recommended_aps)

    return recommended_aps, selected_model, users_per_ap, wire_speed, selected_info

def get_port_speed_above_wire(ap_info: dict, wire_speed: float) -> float:
    """Extract the AP's port speed that is greater than wire_speed.
    
    If none of the available port speeds exceed wire_speed, return the highest available speed.
    """
    port_list = ap_info.get("Port", [])
    speeds = []
    for item in port_list:
        spd = item.get("Speed", [])
        if isinstance(spd, list):
            speeds.extend(spd)
    if not speeds:
        return 1  # Default value if no speed is found
    sorted_speeds = sorted(set(speeds))
    for s in sorted_speeds:
        if s > wire_speed:
            return s
    return max(sorted_speeds)

def get_effective_port_count(switch_info: dict, required_speed: float) -> int:
    effective_count = 0
    for group in switch_info.get("Access", []):
        speeds = group.get("Speed", [])
        if speeds and max(speeds) >= required_speed:
            effective_count += group.get("Ports", 0)
    return effective_count

def calculate_switches(num_aps: int, ap_info: dict):
    ap_power = ap_info.get("Power")
    if not ap_power:
        st.warning("AP model doesn't have a valid Power value.")
        return (None, None, None, None)
    
    # Determine the number of physical ports on the AP (if there are 2 ports, both must connect)
    ap_port_count = sum(item.get("Ports", 0) for item in ap_info.get("Port", []))
    # Total number of AP switch connections required:
    total_ap_connections = num_aps * ap_port_count

    # Get the required port speed threshold from the AP info.
    required_speed = get_port_speed_above_wire(ap_info, wire_speed=0)
    
    best_option = None
    best_switches_needed = None
    margin = 0.7  # 70% available after margin

    for family, switches in SWITCH_MODELS.items():
        for model, info in switches.items():
            effective_port_count = get_effective_port_count(info, required_speed)
            if effective_port_count <= 0:
                continue

            available_ports = math.floor(effective_port_count * margin)
            poe_budget = info.get("PoE Budget", 0)
            poe_limit = math.floor((poe_budget * margin) / ap_power)
            available = min(available_ports, poe_limit)
            if available <= 0:
                continue

            switches_needed = math.ceil(total_ap_connections / available)
            if best_option is None or (best_switches_needed is not None and switches_needed < best_switches_needed):
                best_option = (family, model, info)
                best_switches_needed = switches_needed

    if best_option is None:
        return (None, None, None, None)
    
    # Recalculate available ports for the selected candidate.
    family, model, info = best_option
    effective_port_count = get_effective_port_count(info, required_speed)
    available_ports = math.floor(effective_port_count * margin)
    poe_budget = info.get("PoE Budget", 0)
    poe_limit = math.floor((poe_budget * margin) / ap_power)
    available = min(available_ports, poe_limit)
    
    # Unused ports are those available on all switches minus the total AP connections used.
    unused_ports = (available * best_switches_needed) - total_ap_connections
    total_power_available = best_switches_needed * (poe_budget * margin)
    used_power = num_aps * ap_power
    unused_power = total_power_available - used_power

    return (best_option, best_switches_needed, unused_ports, unused_power)

def format_port_config(switch_info: dict) -> str:
    group_strings = []
    for group in switch_info.get("Access", []):
        ports = group.get("Ports")
        speeds = group.get("Speed", [])
        if ports is not None and speeds:
            speeds_str = "/".join(str(s) for s in speeds)
            group_strings.append(f"{ports} x {speeds_str} Gbps")
    return " + ".join(group_strings)

def render_result_card(title: str, content_html: str, bg_color: str = GLOBAL_BG_COLOR):
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; margin-top: 20px">
        <h2 style="color: {GLOBAL_TEXT_COLOR}; text-align: center;">{title}</h2>
        {content_html}
    </div>
    """, unsafe_allow_html=True)

def render_ap_details(ap_info: dict, ap_model: str):
    ports = sum(item.get("Ports", 0) for item in ap_info.get("Port", []))
    port_speed_list = []
    for item in ap_info.get("Port", []):
        speeds = item.get("Speed", [])
        if speeds:
            port_speed_list.extend(speeds)
    speeds_str = "/".join(str(s) for s in port_speed_list) if port_speed_list else "N/A"
    port_speeds_text = f"{ports} x {speeds_str} Gbps" if speeds_str != "N/A" else "N/A"
    ap_table = f"""
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Antenna Type:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">Omnidirectional Indoor</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Wi-Fi Standard:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{ap_info.get('Wi-Fi Standard')}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Spatial Streams:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{ap_info.get('Spatial Streams')}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">PoE Type:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{ap_info.get('PoE Type')}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Port Speed:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{port_speeds_text}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">SKU:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{ap_info.get('SKU')}</td>
      </tr>
    </table>
    <div style="text-align: center; margin-top: 20px;">
        <a href="{ap_info.get('Datasheet')}" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">Datasheet</a>
        <a href="{ap_info.get('Installation Guide')}" target="_blank" style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Installation Guide</a>
    </div>
    """
    render_result_card(f"Recommended AP Model: <u>{ap_model}</u>", ap_table)

def render_switch_details(switch_option, switches_needed):
    if not switch_option:
        return

    family, switch_model, switch_info = switch_option
    port_config = format_port_config(switch_info)
    
    uplink_list = switch_info.get("Uplink", [])
    if uplink_list:
        uplink_ports = sum(item.get("Ports", 0) for item in uplink_list)
        uplink_speed = " / ".join("/".join(str(s) for s in item.get("Speed", [])) for item in uplink_list)
    else:
        uplink_ports = 0
        uplink_speed = "N/A"

    unit_str = "unit" if switches_needed == 1 else "units"

    switch_table = f"""
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Access Ports:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{port_config}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Uplinks:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{uplink_ports} x {uplink_speed} Gbps</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">PoE Type:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{switch_info.get('PoE Type')}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">PoE Budget:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{switch_info.get('PoE Budget', 0)} W</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">SKU:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{switch_info.get('SKU')}</td>
      </tr>
    </table>
    <div style="text-align: center; margin-top: 20px;">
        <a href="{switch_info.get('Datasheet')}" target="_blank" 
           style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
           Datasheet
        </a>
        <a href="{switch_info.get('Installation Guide')}" target="_blank" 
           style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
           Installation Guide
        </a>
    </div>
    """
    details = f"""
    <div style="margin-bottom: 20px;">
      <p style="font-size: 20px; text-align: center;">
        Based on your AP requirements, you will need <strong>{switches_needed}</strong> {unit_str}.
      </p>
    </div>
    """
    content = details + switch_table
    render_result_card(f"Recommended Access Switch: <u>{switch_model}</u>", content)

def render_bom(recommended_aps, ap_info, switch_option, switches_needed):
    # Prepare each line with no leading spaces
    ap_sku = ap_info.get("SKU", "N/A")
    ap_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">Access Point</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{recommended_aps}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{ap_sku}</td>
</tr>"""

    # AP License row
    ap_license_line = ""
    ap_license_list = ap_info.get("License", [])
    if ap_license_list:
        ap_license_options = ap_license_list[0]
        ap_license_str = f"{ap_license_options.get('Enterprise','')} or {ap_license_options.get('Advanced','')}"
        ap_license_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">AP License</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{recommended_aps}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{ap_license_str}</td>
</tr>"""

    # Switch row(s)
    switch_line = ""
    switch_license_line = ""
    if switch_option is not None:
        _, switch_model, switch_info = switch_option
        switch_sku = switch_info.get("SKU", "N/A")
        switch_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">PoE Access Switch</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{switches_needed}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{switch_sku}</td>
</tr>"""

        switch_license_list = switch_info.get("License", [])
        if switch_license_list:
            switch_license_options = switch_license_list[0]
            switch_license_str = f"{switch_license_options.get('Enterprise','')} or {switch_license_options.get('Advanced','')}"
            switch_license_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">Switch License</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{switches_needed}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{switch_license_str}</td>
</tr>"""
    else:
        switch_line = """<tr style="text-align:center;">
<td style="padding: 10px;">PoE Access Switch</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">0</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">N/A</td>
</tr>"""

    # Now build the table string with everything left-aligned
    bom_html = (
f"""<table style="width: 100%; border-collapse: collapse;">
<tr style="text-align:center;">
<th style="padding: 10px;">Item</th>
<th style="padding: 10px; border-left: 1px solid #ccc;">Quantity</th>
<th style="padding: 10px; border-left: 1px solid #ccc;">Part Number</th>
</tr>
{ap_line}
{ap_license_line}
{switch_line}
{switch_license_line}
</table>

<div style="text-align: center; margin-top: 20px;">
  <p style="font-size: 0.9rem; color: #555;">
    Choose the most appropriate license tier (x = 1, 3, 5, 7, 10 years).
  </p>
</div>
<div style="text-align: center; margin-top: 20px;">
  <a href="https://documentation.meraki.com/General_Administration/Licensing/Meraki_MR_License_Guide"
     target="_blank"
     style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 5px; margin-right: 10px;">
    MR License Guide
  </a>
  <a href="https://documentation.meraki.com/General_Administration/Licensing/Subscription_-_MS_Licensing"
     target="_blank"
     style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 5px;">
    MS License Guide
  </a>
</div>"""
    )

    render_result_card("Bill of Materials (BoM)", bom_html)

def generate_ai_reasoning(
    wifi_generation: str,
    ap_model: str,
    switches_needed: int,
    switch_model: str,
    switch_type: str,
    uplink_ports: int,
    uplink_speed: str,
    users: int,
    area: float,
    recommended_aps: int,
    total_high_speed_ports: int,
    unused_ports: int,
    unused_high_speed_ports: int,
    total_poebudget: int,
    unused_power: int
) -> str:
    ap_generation_dict = AP_MODELS[wifi_generation]
    dict_str = json.dumps(ap_generation_dict, indent=2)
    switch_text = ""
    if switch_model != "N/A":
        switch_text = f"""
To add more context, for the access layer, we're suggesting {switches_needed} unit(s) of switch model {switch_model}. This is a {switch_type} capable model and has {uplink_ports} uplinks ports at {uplink_speed} Gbps.
For the use case, it's remaining {unused_high_speed_ports} unused ports and {unused_power} W of PoE budget left in total.

- Explain why {switches_needed} unit(s) of switch model {switch_model} was chosen. Mention whether it is an L2 or L3 switch, detail its uplink port configuration (number and speeds), and specify that after applying a 30% growth margin, there are {unused_ports} and {unused_power} of unused PoE budget to connect other devices of future growth.
"""
    prompt = f"""
You're a Cisco Networking Expert helping to explain a Meraki wireless network to a partner.
Just for your context, the given scenario is a traditional office environment. We are recommending {recommended_aps} APs model {ap_model} to support {users} users in an area of {area} m².

Follow these instructions strictly to answer:
Return your a concise, direct, and technical explanation without any conversational language or follow-up questions (one-way communication).
Never mention that an certain AP "can support up to XX users" and it's capacity (Mbps).
You don't need to explain the scenario requirements, like "supporting 50 users in a 100 m2 area", the user already knows that.
Don't present redundant information.

- Explain why the AP model {ap_model} was selected, mention if it's for a low or high user density, emphasize its hardware features such as spatial streams, port configuration, and PoE type - without repeating basic scenario details.

{switch_text}

- Finish with a very brief and direct conclusion without being redudant and compare the AP model with an upper or down (if the case) AP model.

For your comparison, below is the list of available AP models:
{dict_str}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt.strip()}],
        max_tokens=300,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

def get_current_scenario_key(results: dict) -> str:
    return (
        f"{results['recommended_aps']}-"
        f"{results['ap_model']}-"
        f"{results['users_per_ap']}-"
        f"{results['wire_speed']}-"
        f"{results['scenario_name']}-"
        f"{results['wifi_generation']}-"
        f"{results['users']}-"
        f"{results['area']}"
    )

def main():
    st.sidebar.image("images/meraki_logo.png", width=150)
    
    st.title("Meraki Wi-Sizer Tool (beta)")
    st.write("Estimate the number of Access Points (APs) and PoE Switches needed for your budgetary Meraki wireless network in an indoor office environment.")

    st.sidebar.header("Input Parameters:")
    users = st.sidebar.number_input("Total Number of Users", min_value=1, max_value=1000, step=5, value=50)
    area = st.sidebar.number_input("Estimated Area (m²)", min_value=20, max_value=2000, step=10, value=100)
    ceiling_height = st.sidebar.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, step=0.1, value=3.0, format="%.1f")
    wifi_generation = st.sidebar.selectbox("Desired Wi-Fi Generation:", ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"])
    st.sidebar.checkbox("Include PoE Access Switches", value=True, key="include_switches")

    st.subheader("Select the most compatible scenario:")
    cols = st.columns(len(SCENARIOS))
    for col, (scenario, data) in zip(cols, SCENARIOS.items()):
        with col:
            try:
                st.image(data.image_path, use_container_width=True)
            except Exception:
                st.write("Image not found.")
            st.caption(f"**{data.name}** {data.description}")

    scenario_type = st.radio(
        label="Select the scenario:",
        options=list(SCENARIOS.keys()),
        format_func=lambda x: SCENARIOS[x].name,
        horizontal=True,
        label_visibility="collapsed"
    )

    if st.button("Calculate"):
        if area <= 0:
            st.warning("Please enter a valid area value.")
        elif users <= 0:
            st.warning("Please enter a valid number of users.")
        else:
            recommended_aps, ap_model, users_per_ap, wire_speed, ap_info = calculate_aps(
                area=area,
                users=users,
                scenario_type=scenario_type,
                wifi_generation=wifi_generation,
                ceiling_height=ceiling_height
            )
            scenario_name = SCENARIOS[scenario_type].name
            st.session_state.calc_results = {
                "recommended_aps": recommended_aps,
                "ap_model": ap_model,
                "users_per_ap": users_per_ap,
                "wire_speed": wire_speed,
                "ap_info": ap_info,
                "scenario_name": scenario_name,
                "wifi_generation": wifi_generation,
                "users": users,
                "area": area
            }
            if "ai_reasoning" in st.session_state:
                del st.session_state.ai_reasoning
            if "scenario_key" in st.session_state:
                del st.session_state.scenario_key

    if "calc_results" in st.session_state:
        results = st.session_state.calc_results

        ap_summary = f"""
        <div style="display: flex; justify-content: space-around; margin-top: 20px;">
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">🏢 Quantity</h3>
                <p style="font-size: 24px; font-weight: bold;">{results['recommended_aps']} AP{'s' if results['recommended_aps'] != 1 else ''}</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">👥 Users/AP</h3>
                <p style="font-size: 24px; font-weight: bold;">{results['users_per_ap']}</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">📡 Wire Speed</h3>
                <p style="font-size: 24px; font-weight: bold;">{results['wire_speed']} Mbps</p>
            </div>
        </div>
        """
        render_result_card("Wireless Sizing Results", ap_summary.strip())
        render_ap_details(results["ap_info"], results["ap_model"])

        switch_option = None
        switches_needed = 0
        switch_model = "N/A"
        total_high_speed_ports = 0
        unused_high_speed_ports = 0
        total_poebudget = 0
        unused_power = 0
        switch_type = "N/A"
        uplink_ports = 0
        uplink_speed = "N/A"

        if st.session_state.include_switches:
            switch_option, switches_needed, unused_ports, unused_power = calculate_switches(results["recommended_aps"], results["ap_info"])
            if switch_option is not None:
                family, switch_model, switch_info = switch_option
                required_speed = get_port_speed_above_wire(results["ap_info"], wire_speed=0)
                high_speed_ports = 0
                for group in switch_info.get("Access", []):
                    speeds = group.get("Speed", [])
                    if speeds and max(speeds) >= required_speed:
                        high_speed_ports += group.get("Ports", 0)
                total_high_speed_ports = high_speed_ports * switches_needed
                ap_ports_required = results["recommended_aps"] * sum(item.get("Ports", 0) for item in results["ap_info"].get("Port", []))
                unused_high_speed_ports = total_high_speed_ports - ap_ports_required

                total_poebudget = switches_needed * switch_info.get("PoE Budget", 0)
                used_power = results["recommended_aps"] * results["ap_info"].get("Power", 0)
                unused_power = total_poebudget - used_power
                switch_type = switch_info.get("Type", "N/A")
                
                uplink_list = switch_info.get("Uplink", [])
                if uplink_list:
                    uplink_ports = sum(item.get("Ports", 0) for item in uplink_list)
                    uplink_speed = " / ".join("/".join(str(s) for s in item.get("Speed", [])) for item in uplink_list)
                else:
                    uplink_ports = 0
                    uplink_speed = "N/A"

                render_switch_details(switch_option, switches_needed)
            else:
                switch_option = None
                switches_needed = 0
                switch_type = "N/A"
                uplink_ports = 0
                uplink_speed = "N/A"
        render_bom(results["recommended_aps"], results["ap_info"], switch_option, switches_needed)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        current_key = get_current_scenario_key(results)
        if "scenario_key" not in st.session_state:
            st.session_state.scenario_key = current_key

        with st.expander("AI Reasoning"):
            if st.session_state.scenario_key != current_key:
                st.session_state.scenario_key = current_key
                if "ai_reasoning" in st.session_state:
                    del st.session_state.ai_reasoning

            if "ai_reasoning" not in st.session_state:
                if st.button("Generate Explanation", key="ai_reasoning_btn"):
                    reasoning_text = generate_ai_reasoning(
                        wifi_generation=results["wifi_generation"],
                        ap_model=results["ap_model"],
                        switches_needed=switches_needed,
                        switch_model=switch_model,
                        switch_type=switch_type,
                        uplink_ports=uplink_ports,
                        uplink_speed=uplink_speed,
                        users=results["users"],
                        area=results["area"],
                        recommended_aps=results["recommended_aps"],
                        total_high_speed_ports=total_high_speed_ports,
                        unused_ports=unused_ports,
                        unused_high_speed_ports=unused_high_speed_ports,
                        total_poebudget=total_poebudget,
                        unused_power=unused_power
                    )
                    st.session_state.ai_reasoning = reasoning_text
            else:
                st.info("Explanation already generated for this scenario. Recalculate to generate a new explanation.")

            if "ai_reasoning" in st.session_state:
                st.markdown(
                    f"<div style='margin-top:10px; text-align:left;'>{st.session_state.ai_reasoning}</div>",
                    unsafe_allow_html=True
                )

        if (
            results["area"] > 1500
            or ceiling_height > 4.5
            or results["users"] > 400
            or results["recommended_aps"] > 12
            or (results["scenario_name"] == "Auditorium" and results["recommended_aps"] >= 5)
        ):
            st.markdown(
                "<div style='text-align: center; color: red; margin-top: 10px;'>"
                "<h4>🚨 Predictive Site Survey Recommended</h4>"
                "<p>Given the complexity, a full site survey is strongly recommended. Contact your SE.</p>"
                "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='text-align: center; color: red; margin-top: 10px;'>"
                "<h4>⚠️ Preliminary Estimation Disclaimer</h4>"
                "<p>This tool provides a preliminary estimation (only recommended for budgetary stages) and doesn't replace a full site survey.</p>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown(
        f"""
        <hr>
        <div style="text-align: center; font-size: 0.8rem; color: #555; margin-top: 20px; margin-bottom: 30px;">
            Designed by Caio Scarpa | Last Updated 02/20/2025
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
