import frappe


def get_api_token():
    acephone_doc = frappe.get_doc("Acephone Integration")

    if not acephone_doc.get("enabled", default=False):
        frappe.throw("Acephone Integration is not enabled!")

    return acephone_doc.get_password("api_token", True)


def get_headers():
    return {
        "Authorization": f"Bearer {get_api_token()}",
    }
