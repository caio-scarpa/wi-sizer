from dataclasses import dataclass
from typing import Dict

@dataclass
class Scenario:
    name: str
    description: str
    coverage_m2: int
    image_path: str

SCENARIOS: Dict[str, Scenario] = {
    "scenario_1": Scenario(
        name="Office 1",
        description="Open office with minimal walls",
        coverage_m2=230,
        image_path="images/cenario_1.png"
    ),
    "scenario_2": Scenario(
        name="Office 2",
        description="Open office with some walls",
        coverage_m2=175,
        image_path="images/cenario_2.png"
    ),
    "scenario_3": Scenario(
        name="Office 3",
        description="Office with several rooms",
        coverage_m2=120,
        image_path="images/cenario_3.png"
    ),
    "auditorium": Scenario(
        name="Auditorium",
        description="High-density room",
        coverage_m2=175,
        image_path="images/auditorio.png"
    )
}

def get_scenario(scenario_type: str) -> Scenario:
    """Retrieve scenario details based on the selected type.
    Returns the default scenario (scenario_1) if the key is not found.
    """
    return SCENARIOS.get(scenario_type, SCENARIOS["scenario_1"])
