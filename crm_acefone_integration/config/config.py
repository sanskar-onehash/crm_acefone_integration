ROLES = {
    "ACEFONE_ADMINISTRATOR": {"role_name": "Acefone Administrator"},
    "ACEFONE_CONNECTOR": {"role_name": "Acefone Connector"},
    "ACEFONE_USER": {"role_name": "Acefone User"},
}

ROLE_KEY_TO_NAME = {}
ROLE_NAME_TO_KEY = {}

for key, value in ROLES.items():
    role_name = value["role_name"]
    ROLE_KEY_TO_NAME[key] = role_name
    ROLE_NAME_TO_KEY[role_name] = key
