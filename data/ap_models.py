AP_MODELS = {
    "Wi-Fi 6": {
        "MR28": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6)",
            "Spatial Streams": "2 x 2 : 2",
            "Port": [
                {"Ports": 1, "Speed": [1]}
            ],
            "PoE Type": "PoE",
            "Power": 15,
            "Capacity": {"2.4GHz": 243.8, "5GHz": 487.5},
            "Max Users": 30,
            "SKU": "MR28-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/MR28_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/MR28_Installation_Guide"
        },
        "MR36": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6)",
            "Spatial Streams": "2 x 2 : 2",
            "Port": [
                {"Ports": 1, "Speed": [1]}
            ],
            "PoE Type": "PoE",
            "Power": 15,
            "Capacity": {"2.4GHz": 243.8, "5GHz": 487.5},
            "Max Users": 35,
            "SKU": "MR36-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/MR36_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/MR36_Installation_Guide"
        },
        "MR44": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6)",
            "Spatial Streams": "2 x 2 : 2 (2.4GHz) + 4 x 4 : 4 (5GHz)",
            "Port": [
                {"Ports": 1, "Speed": [1]}
            ],
            "PoE Type": "PoE+",
            "Power": 30,
            "Capacity": {"2.4GHz": 270.8, "5GHz": 975},
            "Max Users": 45,
            "SKU": "MR44-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/MR44_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/MR44_Installation_Guide"
        },
        "MR46": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6)",
            "Spatial Streams": "4 x 4 : 4",
            "Port": [
                {"Ports": 1, "Speed": [1, 2.5]}
            ],
            "PoE Type": "PoE+",
            "Power": 30,
            "Capacity": {"2.4GHz": 541.7, "5GHz": 1083.3},
            "Max Users": 60,
            "SKU": "MR46-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/MR46_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/MR46_Installation_Guide"
        }
    },
    "Wi-Fi 6E": {
        "CW9162": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6E)",
            "Spatial Streams": "2 x 2 : 2",
            "Port": [
                {"Ports": 1, "Speed": [1, 2.5]}
            ],
            "PoE Type": "PoE+",
            "Power": 30,
            "Capacity": {"2.4GHz": 243.8, "5GHz": 487.5, "6GHz": 487.5},
            "Max Users": 30,
            "SKU": "CW9162I-MR",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/CW9162_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/CW9162_Installation_Guide"
        },
        "CW9164": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6E)",
            "Spatial Streams": "2 x 2 : 2 (2.4GHz) + 4 x 4 : 4 (5GHz) + 4 x 4 : 4 (6GHz)",
            "Port": [
                {"Ports": 1, "Speed": [1, 2.5]}
            ],
            "PoE Type": "PoE+ - USB disabled",
            "Power": 25,
            "Capacity": {"2.4GHz": 243.8, "5GHz": 975, "6GHz": 975},
            "Max Users": 45,
            "SKU": "CW9164I-MR",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/CW9164_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/CW9164_Installation_Guide"
        },
        "CW9166": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6E)",
            "Spatial Streams": "4 x 4 : 4",
            "Port": [
                {"Ports": 1, "Speed": [1, 2.5, 5]}
            ],
            "PoE Type": "PoE+ - USB disabled",
            "Power": 25,
            "Capacity": {"2.4GHz": 541.7, "5GHz": 1083.3, "6GHz": 1083.3},
            "Max Users": 60,
            "SKU": "CW9166I-MR",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/CW9166_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/CW9166_Installation_Guide"
        },
        "MR57": {
            "Wi-Fi Standard": "802.11ax (Wi-Fi 6E)",
            "Spatial Streams": "4 x 4 : 4",
            "Port": [
                {"Ports": 2, "Speed": [1, 2.5, 5]}
            ],
            "PoE Type": "PoE+ - USB disabled",
            "Power": 30,
            "Capacity": {"2.4GHz": 541.7, "5GHz": 1083.3, "6GHz": 1083.3},
            "Max Users": 60,
            "SKU": "MR57-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/MR57_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/MR57_Installation_Guide"
        }
    },
    "Wi-Fi 7": {
        "CW9172": {
            "Wi-Fi Standard": "802.11be (Wi-Fi 7)",
            "Spatial Streams": "2 x 2 : 2",
            "Port": [
                {"Ports": 1, "Speed": [1, 2.5]}
            ],
            "PoE Type": "PoE+ - USB disabled",
            "Power": 25.5,
            "Capacity": {"2.4GHz": 243.8, "5GHz": 487.5, "6GHz": 487.5},
            "Max Users": 30,
            "SKU": "CW9172I-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/CW9172I_%2F%2F_CW9172H_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/CW9172I_Installation_Guide"
        },
        "CW9176": {
            "Wi-Fi Standard": "802.11be (Wi-Fi 7)",
            "Spatial Streams": "4 x 4 : 4",
            "Port": [
                {"Ports": 1, "Speed": [1, 2.5, 5, 10]}
            ],
            "PoE Type": "UPoE",
            "Power": 39,
            "Capacity": {"2.4GHz": 541.7, "5GHz": 1083.3, "6GHz": 2268.5},
            "Max Users": 45,
            "SKU": "CW9176I-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/CW9176I_%2F%2F_CW9176D1_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/CW9176I_Installation_Guide"
        },
        "CW9178": {
            "Wi-Fi Standard": "802.11be (Wi-Fi 7)",
            "Spatial Streams": "4 x 4 : 4",
            "Port": [
                {"Ports": 2, "Speed": [1, 2.5, 5, 10]}
            ],
            "PoE Type": "UPoE",
            "Power": 47,
            "Capacity": {"2.4GHz": 541.7, "5GHz": 1083.3, "6GHz": 2268.5},
            "Max Users": 60,
            "SKU": "CW9178I-HW",
            "License": [
                {"Enterprise": "LIC-ENT-xYR", "Advanced": "LIC-MR-ADV-xYR"}
            ],
            "Datasheet": "https://documentation.meraki.com/MR/MR_Overview_and_Specifications/CW9178I_Datasheet",
            "Installation Guide": "https://documentation.meraki.com/MR/MR_Installation_Guides/CW9178I_Installation_Guide"
        }
    }
}

ap_index = {
    model: details
    for category in AP_MODELS.values()
    for model, details in category.items()
}

def get_ap_model(model: str):
    return ap_index.get(model)
