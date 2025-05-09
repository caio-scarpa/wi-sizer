# -*- coding: utf-8 -*-

import streamlit as st
import math
import pandas as pd
import os
import json
import logging
from typing import Optional, List
from openai import OpenAI
from PIL import Image

# Import scenarios, APs, and switches data modules
from data.scenarios import SCENARIOS, get_scenario
from data.ap_models import AP_MODELS
from data.switch_models import SWITCH_MODELS

# API Key for OpenAI
OPENAI_API_KEY = "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"
if not OPENAI_API_KEY:
    st.error("OpenAI integration problem.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# Page Layout & Container Width
st.set_page_config(
    page_title="Meraki Wi-Sizer Tool",
    page_icon="images/meraki.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "https://outlook.office.com/mail/deeplink/compose?to=cscarpa@cisco.com",
        'About': "Tool created to help you on budgetary wireless calculations. Currently in *beta*."
    }
)

# Google Analytics header
st.markdown("""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-EVS56VM3CC"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-EVS56VM3CC');
    </script>
""", unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO)

def log_calculation(result: dict, ai_explanation: Optional[str] = None, switches_needed: Optional[int] = None,
                    switch_model: Optional[str] = None, source_ip: Optional[str] = "unknown") -> None:
    log_entry = {
         "timestamp": pd.Timestamp.now(),
         "users": result.get("users"),
         "area": result.get("area"),
         "ceiling_height": result.get("ceiling_height"),
         "scenario_name": result.get("scenario_name"),
         "wifi_generation": result.get("wifi_generation"),
         "include_switches": result.get("include_switches"),
         "recommended_aps": result.get("recommended_aps"),
         "ap_model": result.get("ap_model"),
         "switches_needed": switches_needed,
         "switch_model": switch_model,
         "ai_explanation": ai_explanation,
         "source_ip": source_ip
    }
    df = pd.DataFrame([log_entry])
    file_path = "logs.csv"
    df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, sep=";", lineterminator="\n")

# Global Styling Constants
GLOBAL_BG_COLOR = "#F4F4F4"
GLOBAL_TEXT_COLOR = "#27AE60"

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

# ------------------------------
# Helper Functions
# ------------------------------

# Missing function added here
def render_result_card(title: str, content_html: str, bg_color: str = GLOBAL_BG_COLOR) -> None:
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

def format_port_config(switch_info: dict) -> str:
    group_strings = []
    for group in switch_info.get("Access", []):
        ports = group.get("Ports")
        speeds = group.get("Speed", [])
        if ports is not None and speeds:
            speeds_str = "/".join(str(s) for s in speeds)
            group_strings.append(f"{ports} x {speeds_str} Gbps")
    return " + ".join(group_strings)

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
    ap_sku = ap_info.get("SKU", "N/A")
    ap_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">Access Point</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{recommended_aps}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{ap_sku}</td>
</tr>"""
    ap_license_line = ""
    ap_license_list = ap_info.get("License", [])
    if ap_license_list:
        ap_license_options = ap_license_list[0]
        ap_license_str = f"{ap_license_options.get('Enterprise','')} <i>or</i> {ap_license_options.get('Advanced','')}"
        ap_license_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">AP License</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{recommended_aps}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{ap_license_str}*</td>
</tr>"""
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
            switch_license_str = f"{switch_license_options.get('Enterprise','')} <i>or</i> {switch_license_options.get('Advanced','')}"
            switch_license_line = f"""<tr style="text-align:center;">
<td style="padding: 10px;">Switch License</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{switches_needed}</td>
<td style="padding: 10px; border-left: 1px solid #ccc;">{switch_license_str}*</td>
</tr>"""
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
<div style="text-align: center; margin-top: 10px; margin-bottom: 30px;">
  <p style="font-size: 0.9rem; color: #555;">
    *Choose the most appropriate license tier and duration (x = 1, 3, 5, 7, 10 years).<br>
    <u>Ensure that all hardware is certified and approved for use at your location!</u>
  </p>
</div>
<div style="text-align: center; margin-top: 10px;">
  <a href="https://documentation.meraki.com/General_Administration/Licensing/Meraki_MR_License_Guide"
     target="_blank"
     style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 5px; margin-right: 10px;">
    MR License Guide
  </a>
  <a href="https://documentation.meraki.com/General_Administration/Licensing/Subscription_-_MS_Licensing"
     target="_blank"
     style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 5px; margin-right: 10px;">
    MS License Guide
  </a>
    <a href="https://pas.cisco.com/pdtcnc/#/"
     target="_blank"
     style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 5px;">
    Check Country Availability
  </a>
</div>"""
    )
    render_result_card("Bill of Materials (BoM)", bom_html)

@st.cache_data(show_spinner=False)
def calculate_aps(area: float, users: int, scenario_type: str, wifi_generation: str, ceiling_height: float = 3.0):
    concurrency = 0.7  # 70% occupancy
    concurrent_users = users * concurrency
    background_per_user = concurrent_users * 2
    background_devices = 0 if scenario_type == "auditorium" else background_per_user
    throughput_per_user = 5  # Mbps
    background_sync = 0.5  # Mbps

    total_bandwidth = math.ceil((concurrent_users * throughput_per_user) + (background_devices * background_sync))
    
    devices_5ghz = math.ceil((concurrent_users + background_devices) * 0.7)
    scenario_data = get_scenario(scenario_type)
    coverage_m2 = scenario_data.coverage_m2
    
    aps_coverage = math.ceil(area / coverage_m2)
    users_ap = math.ceil(concurrent_users / aps_coverage)
    candidates = []
    for model, info in AP_MODELS[wifi_generation].items():
        if aps_coverage > 5 and model == "MR28":
            continue
        max_users = info.get("Max Users", 0)
        if max_users >= users_ap:
            candidates.append((model, info, max_users))
    if not candidates:
        candidates = [(model, info, info.get("Max Users", 0)) for model, info in AP_MODELS[wifi_generation].items() if not (aps_coverage > 5 and model == "MR28")]
        candidates.sort(key=lambda x: x[2], reverse=True)
        selected_candidate = candidates[0]
    else:
        candidates.sort(key=lambda x: x[2])
        selected_candidate = candidates[0]
    selected_model, selected_info, selected_max_users = selected_candidate

    capacity_24ghz = selected_info.get("Capacity", {}).get("2.4GHz", 0)
    capacity_5ghz = selected_info.get("Capacity", {}).get("5GHz", 0)
    capacity_6ghz = selected_info.get("Capacity", {}).get("6GHz", 0)
    effective_capacity = capacity_5ghz + capacity_6ghz if capacity_6ghz > 0 else capacity_5ghz
    factor = 0.35  # factor to represent real-world data rate
    aps_capacity = math.ceil(total_bandwidth / (effective_capacity * factor)) if effective_capacity > 0 else float('inf')
    aps_density = math.ceil(devices_5ghz / selected_max_users)
    recommended_aps = max(aps_coverage, aps_capacity, aps_density)
    users_per_ap = math.ceil(users / recommended_aps)

    ap_uplink = math.ceil(capacity_24ghz + capacity_5ghz + capacity_6ghz)
    return recommended_aps, selected_model, users_per_ap, ap_uplink, selected_info

def get_port_speed_above_capacity(ap_info: dict, ap_uplink: float) -> float:
    speeds: List[float] = []
    for item in ap_info.get("Port", []):
        spd = item.get("Speed", [])
        if isinstance(spd, list):
            speeds.extend(spd)
    if not speeds:
        return 1
    sorted_speeds = sorted(set(speeds))
    for s in sorted_speeds:
        if s > ap_uplink:
            return s
    return max(sorted_speeds)

@st.cache_data(show_spinner=False)
def calculate_switches(num_aps: int, ap_info: dict, ap_uplink: float):
    ap_power = ap_info.get("Power")
    if not ap_power:
        st.warning("AP model doesn't have a valid Power value.")
        return None, None, None, None
    ap_port_count = sum(item.get("Ports", 0) for item in ap_info.get("Port", []))
    total_ap_connections = num_aps * ap_port_count
    required_speed = get_port_speed_above_capacity(ap_info, ap_uplink=ap_uplink / 1000)
    best_option = None
    best_switches_needed = None
    margin = 0.7  # 70% available after margin
    for family, switches in SWITCH_MODELS.items():
        for model, info in switches.items():
            effective_port_count = sum(group.get("Ports", 0) for group in info.get("Access", []) if group.get("Speed", []) and max(group.get("Speed", [])) >= required_speed)
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
        return None, None, None, None
    family, model, info = best_option
    effective_port_count = sum(group.get("Ports", 0) for group in info.get("Access", []) if group.get("Speed", []) and max(group.get("Speed", [])) >= required_speed)
    available_ports = math.floor(effective_port_count * margin)
    poe_budget = info.get("PoE Budget", 0)
    poe_limit = math.floor((poe_budget * margin) / ap_power)
    available = min(available_ports, poe_limit)
    unused_ports = (available * best_switches_needed) - total_ap_connections
    total_power_available = best_switches_needed * (poe_budget * margin)
    used_power = num_aps * ap_power
    unused_power = total_power_available - used_power
    return best_option, best_switches_needed, unused_ports, unused_power

@st.cache_data(show_spinner=False)
def generate_ai_reasoning(wifi_generation: str, ap_model: str, switches_needed: int, switch_model: str, switch_type: str, uplink_ports: int, uplink_speed: str, users: int, area: float, recommended_aps: int, total_high_speed_ports: int, unused_ports: int, unused_high_speed_ports: int, total_poebudget: int, unused_power: int) -> str:
    ap_generation_dict = AP_MODELS[wifi_generation]
    dict_str = json.dumps(ap_generation_dict, indent=2)
    switch_text = ""
    if switch_model != "N/A":
        switch_text = f"""
To add more context, for the access layer, we're suggesting {switches_needed} unit(s) of switch model {switch_model}. This is a {switch_type} capable model and has {uplink_ports} uplinks ports at {uplink_speed} Gbps.
- Explain why {switches_needed} unit(s) of switch model {switch_model} was chosen. Mention whether it is an L2 or L3 switch, detail its uplink port configuration (number and speeds), and specify that after applying a 30% growth margin, there are {unused_ports} unused ports and {unused_power} W of unused PoE budget to connect other devices or future growth.
"""
    prompt = f"""
You're a Cisco Networking Expert helping to explain a Meraki wireless network to a partner.
For context, the given scenario is a traditional office environment. We're recommending {recommended_aps} APs model {ap_model} to support {users} users in an area of {area} m².
Follow these instructions strictly to answer:
Provide a concise, direct, and technical explanation without any conversational language or follow-up questions.
Don't mention that an certain AP "can support up to XX users" and its capacity (Mbps).
Don't need to explain the scenario requirements, like "supporting 50 users in a 100 m2 area", the user already knows that.
Don't present redundant information.
- Explain why the AP model {ap_model} was selected, mention if it's for a low or high user density, emphasize its hardware features such as spatial streams, port configuration, and PoE type.
{switch_text}
- Finish with a very brief and direct conclusion without being redundant and compare the AP model with an upper or down (if the case) AP model.
For your comparison, below is the list of available AP models:
{dict_str}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt.strip()}],
            max_tokens=300,
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error("Error generating AI reasoning: %s", e)
        return "An error occurred while generating the explanation. Please try again."

def get_current_scenario_key(results: dict) -> str:
    return (
        f"{results['recommended_aps']}-"
        f"{results['ap_model']}-"
        f"{results['users_per_ap']}-"
        f"{results['ap_uplink']}-"
        f"{results['scenario_name']}-"
        f"{results['wifi_generation']}-"
        f"{results['users']}-"
        f"{results['area']}"
    )

# ------------------------------
# Main Application
# ------------------------------
def main():
    st.markdown("""
    <style>
        img {
            border-radius: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True) 

    with st.sidebar:
        st.image("images/meraki_logo.png", width=105)
        scenario_type = st.selectbox(
            label="Select most compatible scenario:",
            options=list(SCENARIOS.keys()),
            format_func=lambda key: SCENARIOS[key].name
        )
        wifi_generation = st.selectbox("Desired Wi-Fi Generation:", ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"])
        users = st.number_input("Total Number of Users", min_value=1, max_value=500, step=5, value=50)

        # Unit toggle and dynamic input parameters
        col1, col2 = st.columns([3, 0.5], gap="small", vertical_alignment="top")
        with col2:
            st.markdown('<span style="font-size:12px;">m -> ft</span>', unsafe_allow_html=True)
            m_ft_toggle = st.toggle("m -> ft", key="m_ft_toggle", label_visibility="collapsed")
        unit = "ft" if m_ft_toggle else "m"

        if unit == "ft":
            # Conversion factors: 1 m² = 10.7639 ft², 1 m = 3.28084 ft
            area_min = 400
            area_max = 16200
            area_step = 200
            area_default = 1200
            ceiling_min = 7.2
            ceiling_max = 16.8
            ceiling_step = 0.6
            ceiling_default = 9.6
            area_label = "Estimated Area (ft²)"
            ceiling_label = "Ceiling Height (ft)"
        else:
            area_min = 40
            area_max = 1400
            area_step = 20
            area_default = 100
            ceiling_min = 2.2
            ceiling_max = 5.2
            ceiling_step = 0.2
            ceiling_default = 3.0
            area_label = "Estimated Area (m²)"
            ceiling_label = "Ceiling Height (m)"
            
        with col1:
            area_input = st.number_input(area_label, min_value=area_min, max_value=area_max, step=area_step, value=area_default)
            ceiling_input = st.number_input(ceiling_label, min_value=ceiling_min, max_value=ceiling_max, step=ceiling_step, value=ceiling_default, format="%.1f")
            
        # Conversion helper functions
        def ft_to_m(feet: float) -> float:
            return feet * 0.3048

        def ft2_to_m2(ft2: float) -> float:
            return ft2 * 0.092903

        if unit == "ft":
            area_m2 = ft2_to_m2(area_input)
            ceiling_m = ft_to_m(ceiling_input)
        else:
            area_m2 = area_input
            ceiling_m = ceiling_input

        include_switches = st.checkbox("Include PoE Access Switch", value=True, key="include_switches")

        space, sub = st.columns([1.8, 1], gap="small", vertical_alignment="top")
        with sub:
            submitted = st.button("Calculate")

    st.write("""
    # Meraki Wi-Sizer Tool _(beta)_
    Estimate the number of Access Points and PoE Switches needed for your budgetary Meraki network in an indoor office environment.
    """)
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    st.subheader("Scenarios:")
    cols = st.columns(len(SCENARIOS))
    for col, (scenario, data) in zip(cols, SCENARIOS.items()):
        with col:
            try:
                st.image(data.image_path, use_container_width=True)
            except Exception:
                st.write("Image not found.")
            st.markdown(
                f"""
                <p style="text-align: center; font-size: 0.9rem; color: grey;">
                    <strong>{data.name}</strong> - {data.description}
                </p>
                """,
                unsafe_allow_html=True
            )

    if submitted:
        if area_m2 <= 0:
            st.warning("Please enter a valid area value.")
        elif users <= 0:
            st.warning("Please enter a valid number of users.")
        else:
            recommended_aps, ap_model, users_per_ap, ap_uplink, ap_info = calculate_aps(
                area=area_m2,
                users=users,
                scenario_type=scenario_type,
                wifi_generation=wifi_generation,
                ceiling_height=ceiling_m
            )
            scenario_name = SCENARIOS[scenario_type].name

            if not include_switches:
                switches_needed = 0
                switch_model = "N/A"
            else:
                switches_needed = 0
                switch_model = "N/A"

            st.session_state.calc_results = {
                "recommended_aps": recommended_aps,
                "ap_model": ap_model,
                "users_per_ap": users_per_ap,
                "ap_uplink": ap_uplink,
                "ap_info": ap_info,
                "scenario_name": scenario_name,
                "wifi_generation": wifi_generation,
                "users": users,
                "area": area_m2,
                "ceiling_height": ceiling_m,
                "include_switches": include_switches
            }
            st.session_state.pop("ai_reasoning", None)
            st.session_state.pop("scenario_key", None)
            log_calculation(
                st.session_state.calc_results,
                switches_needed=switches_needed,
                switch_model=switch_model,
                source_ip="unknown"
            )

    if "calc_results" in st.session_state:
        results = st.session_state.calc_results

        st.divider()        
        
        ap_summary = f"""
        <div style="display: flex; justify-content: space-around;">
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">🏢 Quantity</h3>
                <p style="font-size: 22px; font-weight: bold;">{results['recommended_aps']} AP{'s' if results['recommended_aps'] != 1 else ''}</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">👥 Users/AP</h3>
                <p style="font-size: 22px; font-weight: bold;">{results['users_per_ap']}</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">📡 Estimated Capacity</h3>
                <p style="font-size: 22px; font-weight: bold;">{results['ap_uplink']} Mbps</p>
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
        unused_ports = 0
        switch_type = "N/A"
        uplink_ports = 0
        uplink_speed = "N/A"

        if st.session_state.calc_results.get("include_switches", False):
            switch_option, switches_needed, unused_ports, unused_power = calculate_switches(
                st.session_state.calc_results["recommended_aps"],
                st.session_state.calc_results["ap_info"],
                st.session_state.calc_results["ap_uplink"]
            )
            if switch_option is not None:
                family, switch_model, switch_info = switch_option
                required_speed = get_port_speed_above_capacity(results["ap_info"], ap_uplink=results["ap_uplink"] / 1000)
                high_speed_ports = sum(
                    group.get("Ports", 0)
                    for group in switch_info.get("Access", [])
                    if group.get("Speed", []) and max(group.get("Speed", [])) >= required_speed
                )
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
        if st.session_state.get("scenario_key") != current_key:
            st.session_state["scenario_key"] = current_key
            st.session_state.pop("ai_reasoning", None)

        with st.expander("AI Reasoning"):
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
                    st.session_state["ai_reasoning"] = reasoning_text

                    log_calculation(
                        st.session_state.calc_results,
                        ai_explanation=reasoning_text,
                        switches_needed=switches_needed,
                        switch_model=switch_model,
                        source_ip="unknown"
                    )

            else:
                st.info("Explanation already generated for this scenario. Recalculate to generate a new explanation.")

            if "ai_reasoning" in st.session_state:
                st.markdown(f"<div style='margin-bottom:20px; text-align:left;'>{st.session_state.ai_reasoning}</div>", unsafe_allow_html=True)

        if (
            results["area"] > 1000
            or ceiling_m > 4.5
            or results["users"] > 400
            or results["recommended_aps"] > 12
            or (results["scenario_name"] == "Auditorium" and results["recommended_aps"] >= 5)
        ):
            st.markdown(
                "<div style='text-align: center; color: red'>"
                "<h4>🚨 Predictive Site Survey Recommended</h4>"
                "<p>Given the complexity, a full site survey is strongly recommended. Contact your SE.</p>"
                "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='text-align: center; color: red'>"
                "<h4>⚠️ Preliminary Estimation Disclaimer</h4>"
                "<p>This tool provides a preliminary estimation (only recommended for budgetary stages) and doesn't replace a full site survey.</p>"
                "</div>",
                unsafe_allow_html=True
            )
    st.divider()
    st.markdown(
        f"""
        <div style="text-align: center; font-size: 0.8rem; color: #555; margin-top: 20px; margin-bottom: 30px;">
            Designed by Caio Scarpa | Last Updated 03/05/2025
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
