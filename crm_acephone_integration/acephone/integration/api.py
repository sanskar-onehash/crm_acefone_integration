import frappe
import requests

from crm_acephone_integration.acephone.integration.auth import get_headers


API_VERSION = "v1"
AGENT_STATUS_MAP = ["Enabled", "Blocked", "Disabled" "Busy", "Offline"]


def get_base_uri():
    base_uri = str(frappe.db.get_single_value("Acephone Integration", "base_uri") or "")
    if not base_uri.endswith("/"):
        base_uri += "/"
    return base_uri


def make_get_request(endpoint, params=None):
    return requests.get(
        f"{get_base_uri()}{API_VERSION}/{endpoint}",
        params=params,
        headers=get_headers(),
    )


def make_post_request(endpoint, data=None, json=None, params=None):
    return requests.post(
        f"{get_base_uri()}{API_VERSION}/{endpoint}",
        data=data,
        json=json,
        params=params,
        headers=get_headers(),
    )


def fetch_users():
    has_more = True
    last_seen_id = None
    users = []

    while has_more:
        params = None
        if last_seen_id:
            params = {"last_seen_id": last_seen_id}

        users_res = make_get_request("users", params=params)
        users_res.raise_for_status()

        res_data = users_res.json()
        has_more = res_data.get("has_more", False)
        users_data = res_data.get("data", [])

        data_count = len(users_data)
        last_seen_id = users_data[data_count - 1] if data_count > 0 else None

        for user_data in users_data:
            users.append(format_user_res(user_data))

    return users


def get_refresh_token():
    refresh_res = make_post_request("auth/refresh")
    return {"status": refresh_res.status_code, "text": refresh_res.json()}


def format_user_res(user):
    agent = user.get("agent", {})
    role = user.get("user_role", {})
    return {
        "disabled": not user.get("user_status"),
        "user_id": user.get("id"),
        "user_name": user.get("name"),
        "login_id": user.get("login_id"),
        "extension": user.get("extension"),
        "is_login_based_calling_enabled": user.get("is_login_based_calling_enabled"),
        "is_international_outbound_enabled": user.get(
            "is_international_outbound_enabled"
        ),
        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),
        "agent_status": (
            AGENT_STATUS_MAP[agent.get("status")]
            if agent.get("status", -1) > 0
            and agent.get("status", -1) < len(AGENT_STATUS_MAP)
            else ""
        ),
        "follow_me_number": agent.get("follow_me_number"),
        "role_id": role.get("id"),
        "role_name": role.get("name"),
        "intercom": user.get("intercom"),
    }
