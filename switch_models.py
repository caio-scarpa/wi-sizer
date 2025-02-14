SWITCH_MODELS = {
    "Meraki MS130": {
        "MS130-8P": {
            "Type": "L2",
            "Access Ports": 8,
            "Port Speed (Gbps)": [1],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 120,
            "Uplink Speed (Gbps)": [1],
            "Uplink Ports": 2,
            "SKU": "MS130-8P-HW",
            "Switching Capacity (Gbps)": 20,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/MS130_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/MS130_Series_Installation_Guide"
        },
        "MS130-8X": {
            "Type": "L2",
            "Access Ports": 8,
            "Port Speed": [
                {"Ports": 2, "Speed (Gbps)": [2.5]}, 
                {"Ports": 6, "Speed (Gbps)": [1]}
            ],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 120,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 2,
            "SKU": "MS130-8X-HW",
            "Switching Capacity (Gbps)": 62,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/MS130_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/MS130_Series_Installation_Guide"
        },
        "MS130-12X": {
            "Type": "L2",
            "Access Ports": 12,
            "Port Speed": [
                {"Ports": 4, "Speed (Gbps)": [2.5]}, 
                {"Ports": 8, "Speed (Gbps)": [1]}
            ],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 240,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 2,
            "SKU": "MS130-12X-HW",
            "Switching Capacity (Gbps)": 76,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/MS130_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/MS130_Series_Installation_Guide"
        },
        "MS130-24X": {
            "Type": "L2",
            "Access Ports": 24,
            "Port Speed": [
                {"Ports": 6, "Speed (Gbps)": [2.5]}, 
                {"Ports": 18, "Speed (Gbps)": [1]}
            ],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 370,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "MS130-24X-HW",
            "Switching Capacity (Gbps)": 146,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/MS130_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/MS130_Series_Installation_Guide"
        },
        "MS130-48X": {
            "Type": "L2",
            "Access Ports": 48,
            "Port Speed": [
                {"Ports": 8, "Speed (Gbps)": [2.5]}, 
                {"Ports": 40, "Speed (Gbps)": [1]}
            ],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 740,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "MS130-48X-HW",
            "Switching Capacity (Gbps)": 200,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/MS130_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/MS130_Series_Installation_Guide"
        }
    },
    "Cisco Catalyst C9300L-M": {
        "C9300L-24P-4X-M": {
            "Type": "L3",
            "Access Ports": 24,
            "Port Speed (Gbps)": [1],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 505,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "C9300L-24P-4X-M",
            "Switching Capacity (Gbps)": 128,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/Catalyst_9300L-M_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/Catalyst_9300-M_Series_Installation_Guide"
        },
        "C9300L-24UXG-4X-M": {
            "Type": "L3",
            "Access Ports": 24,
            "Port Speed": [
                {"Ports": 8, "Speed (Gbps)": [1, 2.5, 5, 10]}, 
                {"Ports": 16, "Speed (Gbps)": [1]}
            ],
            "PoE Type": "UPoE",
            "PoE Budget (W)": 880,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "C9300L-24UXG-4X-M",
            "Switching Capacity (Gbps)": 272,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/Catalyst_9300L-M_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/Catalyst_9300-M_Series_Installation_Guide"
        },
        "C9300L-48P-4X-M": {
            "Type": "L3",
            "Access Ports": 48,
            "Port Speed (Gbps)": [1],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 505,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "C9300L-48P-4X-M",
            "Switching Capacity (Gbps)": 176,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/Catalyst_9300L-M_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/Catalyst_9300-M_Series_Installation_Guide"
        },
        "C9300L-48PF-4X-M": {
            "Type": "L3",
            "Access Ports": 48,
            "Port Speed (Gbps)": [1],
            "PoE Type": "PoE+",
            "PoE Budget (W)": 890,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "C9300L-48PF-4X-M",
            "Switching Capacity (Gbps)": 176,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/Catalyst_9300L-M_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/Catalyst_9300-M_Series_Installation_Guide"
        },
        "C9300L-48UXG-4X-M": {
            "Type": "L3",
            "Access Ports": 48,
            "Port Speed": [
                {"Ports": 12, "Speed (Gbps)": [1, 2.5, 5, 10]}, 
                {"Ports": 36, "Speed (Gbps)": [1]}
            ],
            "PoE Type": "UPoE",
            "PoE Budget (W)": 675,
            "Uplink Speed (Gbps)": [10],
            "Uplink Ports": 4,
            "SKU": "C9300L-48UXG-4X-M",
            "Switching Capacity (Gbps)": 392,
            "Datasheet": "https://documentation.meraki.com/MS/MS_Overview_and_Specifications/Catalyst_9300L-M_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MS/MS_Installation_Guides/Catalyst_9300-M_Series_Installation_Guide"
        }
    }
}

def get_switch(model: str):
    """Retrieve switch details based on the model."""
    for family, switches in SWITCH_MODELS.items():
        if model in switches:
            return switches[model]
    return None  # Return None if the model is not found