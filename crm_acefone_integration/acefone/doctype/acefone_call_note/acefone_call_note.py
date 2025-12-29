# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AcefoneCallNote(Document):

    def before_insert(self):
        call_log = frappe.db.exists(
            "Acefone Call Log",
            {
                "call_id": self.call_id,
                "uuid": self.uuid,
                "call_note": ["is", "not set"],
            },
        )
        if call_log:
            frappe.db.set_value("Acefone Call Log", call_log, "call_note", self.name)
