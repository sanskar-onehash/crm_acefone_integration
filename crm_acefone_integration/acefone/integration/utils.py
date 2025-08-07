import frappe
import re
from phonenumbers import parse, format_number, PhoneNumberFormat
from frappe import utils

AGENT_STATUS_MAP = ["Enabled", "Blocked", "Disabled" "Busy", "Offline"]
CALL_TYPES = {
    "INBOUND": "Inbound",
    "OUTBOUND": "Outbound",
    "CLICK_TO_CALL": "Click to Call",
}
DIRECTION_CALL_TYPE_MAP = {
    "inbound": CALL_TYPES["INBOUND"],
    "outbound": CALL_TYPES["OUTBOUND"],
    "clicktocall": CALL_TYPES["CLICK_TO_CALL"],
}
CALL_STATUS_MAP = {"missed": "Missed", "answered": "Answered"}


def format_user_res(user):
    agent = user.get("agent", {})
    role = user.get("user_role", {})
    return {
        "disabled": not user.get("user_status"),
        "user_id": user.get("id"),
        "user_name": user.get("name"),
        "login_id": user.get("login_id"),
        "extension": user.get("extension"),
        "is_login_based_calling_enabled": user.get("is_login_based_calling_enabled"),
        "is_international_outbound_enabled": user.get(
            "is_international_outbound_enabled"
        ),
        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),
        "agent_status": (
            AGENT_STATUS_MAP[agent.get("status")]
            if agent.get("status", -1) >= 0
            and agent.get("status", -1) < len(AGENT_STATUS_MAP)
            else ""
        ),
        "follow_me_number": agent.get("follow_me_number"),
        "role_id": role.get("id"),
        "role_name": role.get("name"),
        "intercom": user.get("intercom"),
    }


def format_call_completed(call_data):
    agent_id = (call_data.get("agent") or {}).get("id")
    acefone_user = None
    if agent_id:
        acefone_user = get_acefone_user_by_agent_id(agent_id)
    else:
        acefone_user = get_acefone_user_by_number(call_data.get("agent_number"))

    return {
        "uuid": call_data.get("uuid"),
        "call_id": call_data.get("call_id"),
        "customer_phone": call_data.get("customer_phone"),
        "caller_id": call_data.get("caller_id"),
        "agent_number": call_data.get("answered_agent_number"),
        "agent_name": call_data.get("answered_agent_name"),
        "acefone_user": acefone_user,
        "missed_agents": get_missed_agents(call_data),
        "call_type": (
            DIRECTION_CALL_TYPE_MAP[call_data.get("direction")]
            if call_data.get("direction")
            else ""
        ),
        "call_status": CALL_STATUS_MAP.get(call_data.get("call_status")),
        "start_stamp": call_data.get("start_stamp"),
        "answer_stamp": call_data.get("answer_stamp"),
        "end_stamp": call_data.get("end_stamp"),
        "billing_second": call_data.get("billing_second"),
        "duration": call_data.get("duration"),
        "agent_ring_time": call_data.get("agent_ring_time"),
        "recording_url": call_data.get("recording_url"),
        "hangup_cause": call_data.get("hangup_cause"),
        "reason_key": call_data.get("reason_key"),
        "call_note": get_call_note_name(call_data),
    }


def get_call_note_name(call_data):
    return frappe.db.exists(
        "Acefone Call Note",
        {"call_id": call_data.get("call_id"), "uuid": call_data.get("uuid")},
    )


def get_linked_doc_for_call_log(call_data):
    # The function definitely requires comments :)
    # Searches for relevant link by priorities:
    # 1. Call Note
    # 2. System Click To Call
    # 3. Setting's Call Log Subscriptions Table

    call_for_doc = None
    linked_doc = None

    if call_data["call_note"]:
        call_note = frappe.get_doc("Acefone Call Note", call_data["call_note"])
        call_for_doc = call_note.note_for
        linked_doc = call_note.linked_doc
    elif call_data["call_type"] == CALL_TYPES["CLICK_TO_CALL"]:
        # Finds the latest click to call log in window of 1 minute before to 30 seconds after
        # the call start_stamp
        start_stamp = utils.get_datetime(call_data["start_stamp"])
        creation_start = utils.add_to_date(start_stamp, minutes=-1, as_datetime=True)
        creation_end = utils.add_to_date(start_stamp, seconds=30, as_datetime=True)

        system_click_to_call = frappe.get_list(
            "Acefone Click To Call Log",
            filters={
                "acefone_user": call_data["acefone_user"],
                "destination": call_data["customer_phone"],
                "creation": ["between", [creation_start, creation_end]],
            },
            order_by="creation desc",
            limit=1,
        )
        if system_click_to_call:
            click_to_call_log = frappe.get_doc(
                "Acefone Click To Call Log", system_click_to_call[0]
            )
            call_for_doc = click_to_call_log.source_doctype
            linked_doc = click_to_call_log.source_doc

    if not call_for_doc:
        customer_normalized_numbers = get_phone_normalized_forms(
            str(call_data["customer_phone"])
        )

        acefone_settings = frappe.get_single("Acefone Integration")
        for cl_subscription in acefone_settings.call_log_subscriptions or []:
            existed_doc = frappe.db.exists(
                cl_subscription.subscribed_for,
                {cl_subscription.phone_fieldname: ["in", customer_normalized_numbers]},
            )
            if existed_doc:
                call_for_doc = cl_subscription.subscribed_for
                linked_doc = existed_doc
                break

    return {"call_for_doc": call_for_doc, "linked_doc": linked_doc}


def get_missed_agents(call_data):
    missed_agents_data = call_data.get("missed_agent") or []
    missed_agents = []

    if isinstance(missed_agents_data, dict):
        missed_agents_data = [missed_agents_data]

    for missed_agent in missed_agents_data:
        missed_agents.append(
            {
                "acefone_user": get_acefone_user_by_number(
                    missed_agent.get("follow_me_number")
                ),
                "agent_name": missed_agent.get("name"),
                "agent_number": missed_agent.get("follow_me_number"),
            }
        )

    return missed_agents


def get_acefone_user_by_agent_id(agent_id, only_enabled=False):
    if agent_id:
        filters = {"agent_id": agent_id}
        if only_enabled:
            filters["disabled"] = 0
        return frappe.get_doc("Acefone User", filters)
    return None


def get_acefone_user_by_number(agent_number, only_enabled=False):
    if agent_number:
        filters = {"follow_me_number": agent_number}
        if only_enabled:
            filters["disabled"] = 0
        return frappe.get_doc("Acefone User", filters)
    return None


def get_acefone_user_by_session(only_enabled=False):
    filters = {"user": frappe.session.user}
    if only_enabled:
        filters["disabled"] = 0

    return frappe.get_doc("Acefone User", filters)


def get_phone_normalized_forms(raw_number: str, default_region=None) -> list[str]:
    try:
        parsed = parse(raw_number, default_region)
        national = str(parsed.national_number)
        intl_e164 = format_number(parsed, PhoneNumberFormat.E164)
        intl_no_plus = intl_e164[1:]
        intl_dash = f"+{parsed.country_code}-{parsed.national_number}"
        return [intl_dash, intl_e164, intl_no_plus, national]
    except Exception:
        return []


def clean_number(number: str | int) -> str:
    return re.sub(r"\D", "", str(number))
