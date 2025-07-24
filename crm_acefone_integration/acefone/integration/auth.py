import frappe


def get_api_token():
    acefone_doc = frappe.get_doc("Acefone Integration")

    if not acefone_doc.get("enabled", default=False):
        frappe.throw("Acefone Integration is not enabled!")

    return acefone_doc.get_password("api_token", True)


def get_headers():
    return {
        "Authorization": f"Bearer {get_api_token()}",
    }
