import frappe
from crm_acephone_integration.config.config import ROLES


def before_install():
    add_acephone_roles()

    frappe.db.commit()


def add_acephone_roles():
    for _, role in ROLES.items():
        role_name = role.get("role_name")
        if role_name and not frappe.db.exists(
            "Role", {"role_name": role.get("role_name")}
        ):
            frappe.get_doc({"doctype": "Role", **role}).insert()
