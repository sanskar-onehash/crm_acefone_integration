import frappe
import requests

from crm_acefone_integration.acefone.integration.auth import get_headers
from crm_acefone_integration.acefone.integration import utils
from crm_acefone_integration.config.config import ROLE_KEY_TO_NAME


API_VERSION = "v1"


def get_base_uri():
    base_uri = str(frappe.db.get_single_value("Acefone Integration", "base_uri") or "")
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
        frappe.log_error("res", res_data)
        has_more = res_data.get("has_more", False)
        users_data = res_data.get("data", [])

        data_count = len(users_data)
        last_seen_id = users_data[data_count - 1] if data_count > 0 else None

        for user_data in users_data:
            users.append(utils.format_user_res(user_data))

    return users


@frappe.whitelist()
def click_to_call(destination_number, source_doctype, source_name, acefone_user=None):
    if acefone_user:
        if ROLE_KEY_TO_NAME["ACEFONE_ADMINISTRATOR"] in frappe.get_roles():
            acefone_user = frappe.get_doc("Acefone User", acefone_user)
    else:
        acefone_user = utils.get_acefone_user_by_session(only_enabled=True)

    if not acefone_user:
        frappe.throw("User don't have corresponding enabled acefone agent.")

    res = make_post_request(
        "click_to_call",
        data={
            "agent_number": acefone_user.get("agent_id"),
            "destination_number": destination_number,
        },
    )
    res.raise_for_status()

    frappe.get_doc(
        {
            "acefone_user": acefone_user.get("name"),
            "destination": utils.clean_number(destination_number),
            "doctype": "Acefone Click To Call Log",
            "source_doc": source_name,
            "source_doctype": source_doctype,
        }
    ).save()
    return res.json()
