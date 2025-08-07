# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

CALL_LOGS_FETCH_LIMIT = 50


class AcefoneCallLog(Document):
    pass


@frappe.whitelist()
def get_call_logs(doctype, docname, page=0):
    if not doctype or not docname:
        return []

    return frappe.get_list(
        "Acefone Call Log",
        filters={
            "call_for_doc": doctype,
            "linked_doc": docname,
        },
        fields=[
            "call_type",
            "customer_phone",
            "caller_id",
            "call_status",
            "start_stamp",
            "duration",
            "recording_url",
        ],
        order_by="start_stamp desc",
        limit_start=page * CALL_LOGS_FETCH_LIMIT,
        limit_page_length=CALL_LOGS_FETCH_LIMIT,
    )
