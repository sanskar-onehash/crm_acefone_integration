import frappe
import requests

from crm_acephone_integration.acephone.integration.auth import get_headers
from crm_acephone_integration.acephone.integration import utils


API_VERSION = "v1"


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
            users.append(utils.format_user_res(user_data))

    return users
