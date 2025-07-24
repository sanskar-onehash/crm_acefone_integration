# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from crm_acefone_integration.acefone.integration.api import fetch_users

SYNC_ACEFONE_TIMEOUT = 25 * 60
SYNC_ACEFONE_JOB_NAME = "sync_acefone_users"
PROGRESS_ID = "sync_acefone_users"


class AcefoneUser(Document):
    pass


@frappe.whitelist()
def sync_acefone_users():
    frappe.enqueue(
        _sync_acefone_users,
        queue="default",
        timeout=SYNC_ACEFONE_TIMEOUT,
        job_name=SYNC_ACEFONE_JOB_NAME,
    )
    return {
        "status": "success",
        "msg": "Acefone Users syncing started in background.",
        "track_on": PROGRESS_ID,
    }


def _sync_acefone_users():
    acefone_users = fetch_users()
    total = len(acefone_users)

    for idx, user in enumerate(acefone_users):
        frappe.publish_realtime(
            PROGRESS_ID,
            {"progress": idx + 1, "total": total, "title": "Syncing Acefone Users"},
        )
        existing_user = frappe.db.exists(
            "Acefone User", {"user_id": user.get("user_id")}
        )
        user_doc = None
        if existing_user:
            user_doc = frappe.get_doc("Acefone User", existing_user)
            has_updated = False
            for fieldname, new_value in user.items():
                old_value = user_doc.get(fieldname)

                if isinstance(new_value, int) and not isinstance(new_value, bool):
                    new_value = str(new_value)

                if isinstance(new_value, bool):
                    has_changed = new_value != bool(old_value)
                else:
                    has_changed = new_value != old_value

                if has_changed:
                    user_doc.set(fieldname, new_value)
                    has_updated = True

            if has_updated:
                user_doc.save()
        else:
            frappe.get_doc({"doctype": "Acefone User", **user}).save()
    frappe.db.commit()
