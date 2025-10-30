import frappe

from crm_acefone_integration.acefone.integration import utils

CALL_ANSWERED_EVENT = "agent_answered_call"
CALL_LOG_ADDED_EVENT = "acefone_call_log_added"


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

    now_datetime = frappe.utils.get_datetime()
    creation_start = frappe.utils.add_to_date(
        now_datetime, minutes=-5, as_datetime=True
    )
    creation_end = frappe.utils.add_to_date(now_datetime, seconds=30, as_datetime=True)

    c2c_log_values = frappe.db.get_value(
        "Acefone Click To Call Log",
        {
            "acefone_user": acefone_user.name,
            "destination": ["in", possible_phone_forms],
            "creation": ["between", [creation_start, creation_end]],
        },
        ["source_doc", "source_doctype"],
        as_dict=True,
    )
    if c2c_log_values:
        if not message["linked_doc"]:
            message["note_for"] = c2c_log_values.get("source_doctype")
            message["linked_doc"] = c2c_log_values.get("source_doc")

        frappe.publish_realtime(
            CALL_ANSWERED_EVENT,
            message,
            user=user,
            doctype=c2c_log_values.get("source_doctype") or None,
            docname=c2c_log_values.get("source_doc") or None,
        )
    else:
        frappe.publish_realtime(CALL_ANSWERED_EVENT, message, user=user)


def handle_call_complete(call_data):
    try:
        call_data = utils.format_call_completed(call_data)

        linked_doc = utils.get_linked_doc_for_call_log(call_data)
        call_log_doc = frappe.get_doc(
            {
                "doctype": "Acefone Call Log",
                **linked_doc,
                **call_data,
            }
        ).save()

        frappe.publish_realtime(
            CALL_LOG_ADDED_EVENT,
            {
                "call_log": call_log_doc.name,
                "call_for_doc": call_log_doc.call_for_doc,
                "linked_doc": call_log_doc.linked_doc,
            },
            after_commit=True,
        )
    except Exception as e:
        frappe.log_error("error occured in acefone handle_call_complete", e)
