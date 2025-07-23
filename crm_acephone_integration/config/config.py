ROLES = {
    "ACEPHONE_ADMINISTRATOR": {"role_name": "Acephone Administrator"},
    "ACEPHONE_CONNECTOR": {"role_name": "Acephone Connector"},
    "ACEPHONE_USER": {"role_name": "Acephone User"},
}

ROLE_KEY_TO_NAME = {}
ROLE_NAME_TO_KEY = {}

for key, value in ROLES.items():
    role_name = value["role_name"]
    ROLE_KEY_TO_NAME[key] = role_name
    ROLE_NAME_TO_KEY[role_name] = key
