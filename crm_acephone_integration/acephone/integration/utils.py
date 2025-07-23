import frappe
from phonenumbers import parse, format_number, PhoneNumberFormat

AGENT_STATUS_MAP = ["Enabled", "Blocked", "Disabled" "Busy", "Offline"]
DIRECTION_CALL_TYPE_MAP = {"inbound": "Inbound", "outbound": "Outbound"}


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
            if agent.get("status", -1) > 0
            and agent.get("status", -1) < len(AGENT_STATUS_MAP)
            else ""
        ),
        "agent_number": agent.get("follow_me_number"),
        "role_id": role.get("id"),
        "role_name": role.get("name"),
        "intercom": user.get("intercom"),
    }


def format_call_completed(call_data):
    return {
        "uuid": call_data.get("uuid"),
        "call_id": call_data.get("call_id"),
        "customer_phone": call_data.get("customer_phone"),
        "caller_id": call_data.get("caller_id"),
        "agent_number": call_data.get("answered_agent_number"),
        "agent_name": call_data.get("answered_agent_name"),
        "acephone_user": get_acephone_user_by_number(call_data.get("agent_number")),
        "missed_agents": get_missed_agents(call_data),
        "call_type": (
            DIRECTION_CALL_TYPE_MAP[call_data.get("direction")]
            if call_data.get("direction")
            else ""
        ),
        "call_status": call_data.get("call_status"),
        "start_stamp": call_data.get("start_stamp"),
        "answer_stamp": call_data.get("answer_stamp"),
        "end_stamp": call_data.get("end_stamp"),
        "billing_second": call_data.get("billing_second"),
        "duration": call_data.get("duration"),
        "agent_ring_time": call_data.get("agent_ring_time"),
        "recording_url": call_data.get("recording_url"),
        "hangup_cause": call_data.get("hangup_cause"),
        "call_note": get_call_note_name(call_data),
    }


def get_call_note_name(call_data):
    return frappe.db.exists(
        "Acephone Call Note",
        {"call_id": call_data.get("call_id"), "uuid": call_data.get("uuid")},
    )


def get_missed_agents(call_data):
    missed_agents_data = call_data.get("missed_agent")
    missed_agents = []

    if isinstance(missed_agents_data, dict):
        missed_agents_data = [missed_agents_data]

    for missed_agent in missed_agents_data:
        missed_agents.append(
            {
                "acephone_user": get_acephone_user_by_number(
                    missed_agent.get("follow_me_number")
                ),
                "agent_name": missed_agent.get("name"),
                "agent_number": missed_agent.get("follow_me_number"),
            }
        )

    return missed_agents


def get_acephone_user_by_number(agent_number):
    if agent_number:
        return frappe.get_doc("Acephone User", {"agent_number": agent_number})
    return None


def get_phone_normalized_forms(raw_number: str, default_region="IN") -> list[str]:
    try:
        parsed = parse(raw_number, default_region)
        national = str(parsed.national_number)
        intl_e164 = format_number(parsed, PhoneNumberFormat.E164)
        intl_no_plus = intl_e164[1:]
        intl_dash = f"+{parsed.country_code}-{parsed.national_number}"
        return [intl_dash, intl_e164, intl_no_plus, national]
    except Exception:
        return []
