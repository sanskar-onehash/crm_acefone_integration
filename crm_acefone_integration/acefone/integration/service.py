import frappe

from crm_acefone_integration.acefone.integration import utils

CALL_ANSWERED_EVENT = "agent_answered_call"


def handle_call_answered_by_agent(call_data):
    acefone_user = utils.get_acefone_user_by_number(call_data.get("agent_number"))
    if not acefone_user:
        return

    user = acefone_user.get("user")
    if not user:
        return

    possible_phone_forms = utils.get_phone_normalized_forms(
        call_data.get("customer_phone")
    )
    message = {
        "call_id": call_data.get("call_id"),
        "uuid": call_data.get("uuid"),
        "customer_phone": call_data.get("customer_phone"),
        "acefone_user": acefone_user.get("name"),
        "note_for": None,
        "linked_doc": None,
    }

    for subscription in acefone_user.get("call_subscriptions") or []:
        existed_doc = frappe.db.exists(
            subscription.get("subscribed_for"),
            {subscription.get("phone_fieldname"): ["in", possible_phone_forms]},
        )
        if existed_doc:
            message["note_for"] = subscription.get("subscribed_for")
            message["linked_doc"] = existed_doc
            break

    frappe.publish_realtime(CALL_ANSWERED_EVENT, message, user=user)


def handle_call_complete(call_data):
    call_data = utils.format_call_completed(call_data)
    linked_doc = utils.get_linked_doc_for_call_log(call_data)

    frappe.get_doc(
        {
            "doctype": "Acefone Call Log",
            **linked_doc,
            **call_data,
        }
    ).save()
