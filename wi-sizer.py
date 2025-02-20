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
    page_title="Meraki Wi-Sizer Tool",
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

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def calculate_aps(area: float, users: int, scenario_type: str, wifi_generation: str, ceiling_height: float = 3.0):
    concurrency = 0.7
    concurrent_users = users * concurrency
    background_per_user = concurrent_users * 2

    throughput_per_user = 4
    background_sync = 0.5

    scenario_data = get_scenario(scenario_type)
    coverage_per_ap = scenario_data["coverage_m2"]
    max_users_per_ap = scenario_data["max_users_per_ap"]

    background_devices = 0 if scenario_type == "auditorium" else background_per_user
    devices_5ghz = math.ceil((concurrent_users + background_devices) * 0.7)
    total_bandwidth = math.ceil((concurrent_users * throughput_per_user) + (background_devices * background_sync))

    ap_capacity = 180 * 0.8

    aps_capacity = math.ceil(total_bandwidth / ap_capacity)
    aps_coverage = math.ceil(area / coverage_per_ap)
    aps_density = math.ceil(devices_5ghz / max_users_per_ap)
    recommended_aps = max(aps_capacity, aps_coverage, aps_density)

    effective_users_per_ap = math.ceil(devices_5ghz / recommended_aps)
    users_per_ap = math.ceil(users / recommended_aps)
    bandwidth_per_ap = round(total_bandwidth / recommended_aps, 0)

    # Simplified logic for selecting AP model
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
    return recommended_aps, ap_model, users_per_ap, effective_users_per_ap, bandwidth_per_ap, ap_info

def get_effective_port_count(switch_info: dict, required_speed: float) -> int:
    effective_count = 0
    for group in switch_info.get("Port Speed", []):
        speeds = group.get("Speed (Gbps)", [])
        if speeds and max(speeds) >= required_speed:
            effective_count += group.get("Ports", 0)
    return effective_count

def calculate_switches(num_aps: int, ap_info: dict):
    ap_power = ap_info.get("PoE")
    if not ap_power:
        st.warning("AP model doesn't have a valid PoE value.")
        return (None, None)

    port_speed = ap_info.get("Port Speed", [])
    required_speed = max(port_speed) if (isinstance(port_speed, list) and port_speed and all(isinstance(s, (int, float)) for s in port_speed)) else 1

    best_option = None
    best_switches_needed = None
    margin = 0.7

    for family, switches in SWITCH_MODELS.items():
        for model, info in switches.items():
            effective_port_count = get_effective_port_count(info, required_speed)
            if effective_port_count <= 0:
                continue

            available_ports = math.floor(effective_port_count * margin)
            poe_budget = info.get("PoE Budget (W)", 0)
            poe_limit = math.floor((poe_budget * margin) / ap_power)
            available = min(available_ports, poe_limit)
            if available <= 0:
                continue

            switches_needed = math.ceil(num_aps / available)
            if best_option is None or (best_switches_needed is not None and switches_needed < best_switches_needed):
                best_option = (family, model, info)
                best_switches_needed = switches_needed

    return (best_option, best_switches_needed)

def format_port_config(switch_info: dict) -> str:
    group_strings = []
    for group in switch_info.get("Port Speed", []):
        ports = group.get("Ports")
        speeds = group.get("Speed (Gbps)", [])
        if ports is not None and speeds:
            speeds_str = "/".join(str(s) for s in speeds)
            group_strings.append(f"{ports} x {speeds_str} Gbps")
    return " + ".join(group_strings)

def render_result_card(title: str, content_html: str, bg_color: str = GLOBAL_BG_COLOR):
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; margin-top: 20px;">
        <h2 style="color: {GLOBAL_TEXT_COLOR}; text-align: center;">{title}</h2>
        {content_html}
    </div>
    """, unsafe_allow_html=True)

def render_ap_details(ap_info: dict, ap_model: str):
    ports = ap_info.get("Ports", 1)
    port_speed_list = [str(speed) for speed in ap_info.get('Port Speed', []) if isinstance(speed, (int, float))]
    speeds_str = "/".join(port_speed_list)
    port_speeds_text = f"{ports} x {speeds_str} Gbps" if speeds_str else "N/A"
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
        return  # No switch to render

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

    switch_table = f"""
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Access Ports:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{port_config}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">Uplinks:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{uplink_info}</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">PoE Budget:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{switch_info.get('PoE Budget (W)', 0)} W</td>
      </tr>
      <tr>
        <td style="font-weight: bold; width: 30%; padding: 10px; text-align: left;">PoE Type:</td>
        <td style="width: 70%; padding: 10px; text-align: left;">{switch_info.get('PoE Type')}</td>
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
    # Build the Access Point row (always shown)
    ap_sku = ap_info.get("SKU", "N/A")
    ap_line = f"""
    <tr style="text-align: center;">
        <td style="padding: 10px;">Access Point</td>
        <td style="padding: 10px; border-left: 1px solid #ccc;">{recommended_aps}</td>
        <td style="padding: 10px; border-left: 1px solid #ccc;">{ap_sku}</td>
    </tr>
    """
    
    # Always build the PoE Access Switch row
    # If no switch option is provided, default to 0 quantity and "N/A" for SKU.
    if switch_option is not None:
        family, switch_model, switch_info = switch_option
        switch_sku = switch_info.get("SKU", "N/A")
        switch_quantity = switches_needed if switches_needed is not None else 0
    else:
        switch_model = "N/A"
        switch_sku = "N/A"
        switch_quantity = 0

    switch_line = f"""
    <tr style="text-align: center;">
        <td style="padding: 10px;">PoE Access Switch</td>
        <td style="padding: 10px; border-left: 1px solid #ccc;">{switch_quantity}</td>
        <td style="padding: 10px; border-left: 1px solid #ccc;">{switch_sku}</td>
    </tr>
    """

    bom_html = f"""
    <table style="width: 100%; border-collapse: collapse;">
      <tr style="text-align: center;">
        <th style="padding: 10px;">Item</th>
        <th style="padding: 10px; border-left: 1px solid #ccc;">Quantity</th>
        <th style="padding: 10px; border-left: 1px solid #ccc;">Part Number</th>
      </tr>
      {ap_line}
      {switch_line}
    </table>
    <div style="text-align: center; margin-top: 20px;">
      <a href="https://www.merakisizing.com/" target="_blank"
         style="background-color: {GLOBAL_TEXT_COLOR}; color: white; padding: 10px 20px;
                text-decoration: none; border-radius: 5px;">
         Licensing Info
      </a>
    </div>
    """
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
    effective_users: int,
    recommended_aps: int,
    total_high_speed_ports: int,
    unused_high_speed_ports: int,
    total_poebudget: int,
    unused_power: int
) -> str:
    """
    Build the prompt. If switch_model == "N/A", skip the switch text.
    """
    ap_generation_dict = AP_MODELS[wifi_generation]
    dict_str = json.dumps(ap_generation_dict, indent=2)

    switch_text = ""
    if switch_model != "N/A":
        switch_text = f"""
For the access layer, {switches_needed} unit(s) of switch model {switch_model} were selected.
This switch is {switch_type} and features {uplink_ports} uplink ports at {uplink_speed} Gbps.
After a 30% growth margin is applied, there remain {unused_high_speed_ports} unused ports and {unused_power} W of PoE budget available.
Then, explain why {switches_needed} unit(s) of switch model {switch_model} was chosen. Mention whether it is an L2 or L3 switch, detail its uplink port configuration (number and speeds), and specify that after applying a 30% growth margin, there are {unused_high_speed_ports} unused high-speed ports and {unused_power} W of unused PoE budget.
"""

    prompt = f"""
You're a Cisco Networking Expert and is helping a partner to size a Meraki wireless network for a traditional office scenario. Provide a concise, one-way technical explanation.

Answer instructions:
Return your answer as a single, direct technical paragraph without any conversational language or follow-up questions.
Never mention that an certain AP "can support up to XX users" and it's capacity in Mbps.
You don't need to explain the scenario again, like "supporting 50 users in a 100 m2 area", the user already knows that.

Just for your context, for a given office scenario, we recommend {recommended_aps} APs of model {ap_model} to support {users} users in a {area} m2 area,  each AP supporting about {effective_users} users. Explain why the AP model {ap_model} was selected, emphasizing its hardware features such as spatial streams, port configuration, and PoE type—without repeating basic scenario details.

{switch_text}

Conclude with a brief summary of the overall hardware selection without being too redudant and why the AP works good with the Switch (if mentioned) selected.

Below is the list of available AP models for {wifi_generation}:
{dict_str}


"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt.strip()}],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def get_current_scenario_key(results: dict) -> str:
    return (
        f"{results['recommended_aps']}-"
        f"{results['ap_model']}-"
        f"{results['users_per_ap']}-"
        f"{results['effective_users_per_ap']}-"
        f"{results['bandwidth_per_ap']}-"
        f"{results['scenario_name']}-"
        f"{results['wifi_generation']}-"
        f"{results['users']}-"
        f"{results['area']}"
    )

def main():
    st.sidebar.image("images/meraki_logo.png", width=150)
    
    st.title("Meraki Wi-Sizer Tool")
    st.write("Estimate the number of Access Points (APs) and PoE Switches needed for your Meraki wireless network in an indoor office environment.")

    st.sidebar.header("Input Parameters:")
    users = st.sidebar.number_input("Total Number of Users", min_value=1, step=5, value=50)
    area = st.sidebar.number_input("Estimated Area (m²)", min_value=20, step=10, value=100)
    ceiling_height = st.sidebar.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, step=0.1, value=3.0, format="%.1f")
    wifi_generation = st.sidebar.selectbox("Select the Wi-Fi Generation:", ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"])
    st.sidebar.checkbox("Include PoE Access Switches", value=True, key="include_switches")

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
            recommended_aps, ap_model, users_per_ap, effective_users_per_ap, bandwidth_per_ap, ap_info = calculate_aps(
                area=area,
                users=users,
                scenario_type=scenario_type,
                wifi_generation=wifi_generation,
                ceiling_height=ceiling_height
            )
            scenario_name = SCENARIOS[scenario_type]["name"]
            st.session_state.calc_results = {
                "recommended_aps": recommended_aps,
                "ap_model": ap_model,
                "users_per_ap": users_per_ap,
                "effective_users_per_ap": effective_users_per_ap,
                "bandwidth_per_ap": bandwidth_per_ap,
                "ap_info": ap_info,
                "scenario_name": scenario_name,
                "wifi_generation": wifi_generation,
                "users": users,
                "area": area
            }
            # Clear any old explanation state
            if "ai_reasoning" in st.session_state:
                del st.session_state.ai_reasoning
            if "scenario_key" in st.session_state:
                del st.session_state.scenario_key

    if "calc_results" in st.session_state:
        results = st.session_state.calc_results

        # Display AP Sizing Results
        ap_summary = f"""
        <div style="display: flex; justify-content: space-around; margin-top: 20px;">
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">🏢 Quantity</h3>
                <p style="font-size: 24px; font-weight: bold;">{results['recommended_aps']} AP{'s' if results['recommended_aps'] != 1 else ''}</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">👥 Density</h3>
                <p style="font-size: 24px; font-weight: bold;">{results['users_per_ap']} Users/AP</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: {GLOBAL_TEXT_COLOR};">📡 Capacity</h3>
                <p style="font-size: 24px; font-weight: bold;">{round(results['bandwidth_per_ap'])} Mbps/AP</p>
            </div>
        </div>
        """
        render_result_card("Wireless Sizing Results", ap_summary.strip())
        render_ap_details(results["ap_info"], results["ap_model"])

        # Initialize default (no switch)
        switch_option = None
        switches_needed = None
        switch_model = "N/A"
        total_high_speed_ports = 0
        unused_high_speed_ports = 0
        total_poebudget = 0
        unused_power = 0
        switches_needed = 0
        switch_type = "N/A"
        uplink_ports = 0
        uplink_speed = "N/A"

        # If toggled on, compute switch
        if st.session_state.include_switches:
            switch_option, switches_needed = calculate_switches(results["recommended_aps"], results["ap_info"])
            if switch_option is not None:
                family, switch_model, switch_info = switch_option
                required_speed = max(results["ap_info"].get("Port Speed", [1]))
                high_speed_ports = 0
                for group in switch_info.get("Port Speed", []):
                    speeds = group.get("Speed (Gbps)", [])
                    if speeds and max(speeds) >= required_speed:
                        high_speed_ports += group.get("Ports", 0)

                total_high_speed_ports = high_speed_ports * switches_needed
                ap_ports_required = results["recommended_aps"] * results["ap_info"].get("Ports", 1)
                unused_high_speed_ports = total_high_speed_ports - ap_ports_required

                total_poebudget = switches_needed * switch_info.get("PoE Budget (W)", 0)
                used_power = results["recommended_aps"] * results["ap_info"].get("PoE", 0)
                unused_power = total_poebudget - used_power
                switch_type = switch_info.get("Type", "N/A")
                uplink_ports = switch_info.get("Uplink Ports", 0)
                uplink_speed_list = switch_info.get("Uplink Speed (Gbps)", [])
                uplink_speed = ", ".join(str(s) for s in uplink_speed_list) if uplink_speed_list else "N/A"

                render_switch_details(switch_option, switches_needed)
            else:
                switch_option = None
                switches_needed = 0
                switch_type = "N/A"
                uplink_ports = 0
                uplink_speed = "N/A"
        render_bom(results["recommended_aps"], results["ap_info"], switch_option, switches_needed)

        # Add spacing above the AI Explanation expander
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        # Build a unique scenario key
        def get_current_scenario_key(results: dict) -> str:
            return (
                f"{results['recommended_aps']}-"
                f"{results['ap_model']}-"
                f"{results['users_per_ap']}-"
                f"{results['effective_users_per_ap']}-"
                f"{results['bandwidth_per_ap']}-"
                f"{results['scenario_name']}-"
                f"{results['wifi_generation']}-"
                f"{results['users']}-"
                f"{results['area']}"
            )

        current_key = get_current_scenario_key(results)
        if "scenario_key" not in st.session_state:
            st.session_state.scenario_key = current_key

        with st.expander("AI Reasoning"):
            # If the scenario changed, reset explanation
            if st.session_state.scenario_key != current_key:
                st.session_state.scenario_key = current_key
                if "ai_reasoning" in st.session_state:
                    del st.session_state.ai_reasoning

            # Let user click once
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
                        effective_users=results["effective_users_per_ap"],
                        recommended_aps=results["recommended_aps"],
                        total_high_speed_ports=total_high_speed_ports,
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

        # Disclaimer
        if (
            results["area"] > 1200
            or ceiling_height > 4.5
            or results["users"] > 500
            or results["recommended_aps"] > 12
            or (results["scenario_name"] == "Auditorium" and results["recommended_aps"] >= 5)
        ):
            st.markdown(
                "<div style='text-align: center; color: red; margin-top: 20px;'>"
                "<h4>🚨 Predictive Site Survey Recommended</h4>"
                "<p>Given the complexity, a full site survey is strongly recommended. Contact your SE.</p>"
                "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='text-align: center; color: red; margin-top: 20px;'>"
                "<h4>⚠️ Preliminary Estimation Disclaimer</h4>"
                "<p>This tool provides a preliminary estimation and doesn't replace a full site survey.</p>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown(
        f"""
        <hr>
        <div style="text-align: center; font-size: 0.8rem; color: #555; margin-top: 20px; margin-bottom: 40px;">
            Designed by Caio Scarpa | Last Updated 02/19/2025
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
