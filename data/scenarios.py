SCENARIOS = {
    "scenario_1": {
        "name": "Office 1",
        "description": " – Open office w/ minimal walls",
        "coverage_m2": 230,
        "max_users_per_ap": 35,
        "img": "images/cenario_1.png"
    },
    "scenario_2": {
        "name": "Office 2",
        "description": " – Open office w/ some walls",
        "coverage_m2": 175,
        "max_users_per_ap": 30,
        "img": "images/cenario_2.png"
    },
    "scenario_3": {
        "name": "Office 3",
        "description": " – Office w/ several rooms",
        "coverage_m2": 120,
        "max_users_per_ap": 25,
        "img": "images/cenario_3.png"
    },
    "auditorium": {
        "name": "Auditorium",
        "description": " – High-density room",
        "coverage_m2": 175,
        "max_users_per_ap": 50,
        "img": "images/auditorio.png"
    }
}

def get_scenario(scenario_type: str):
    """Retrieve scenario details based on the selected type."""
    return SCENARIOS.get(scenario_type, SCENARIOS["scenario_1"])
