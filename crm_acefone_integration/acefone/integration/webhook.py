import frappe


from crm_acefone_integration.acefone.integration import service


@frappe.whitelist()
def inbound_answered_by_agent():
    service.handle_call_answered_by_agent(frappe.form_dict)


@frappe.whitelist()
def outbound_answered_by_agent():
    service.handle_call_answered_by_agent(frappe.form_dict)


@frappe.whitelist()
def inbound_call_complete():
    service.handle_call_complete(frappe.form_dict)


@frappe.whitelist()
def outbound_call_complete():
    service.handle_call_complete(frappe.form_dict)
