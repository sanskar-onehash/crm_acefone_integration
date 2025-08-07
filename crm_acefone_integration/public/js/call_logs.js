const CALL_LOG_ADDED_EVENT = "acefone_call_log_added";
const ACEFONE_CALL_LOGS_FIELD = "acefone_call_logs_html";

const acefone_hooked_doctypes = new Set();
$(document).on("form-refresh", function (_, frm) {
  if (!frm || !frm.doctype) return;
  if (acefone_hooked_doctypes.has(frm.doctype)) return;

  acefone_hooked_doctypes.add(frm.doctype);
  frappe.ui.form.on(frm.doctype, {
    async refresh(frm) {
      if (!frm.docname || frm.__acefone_logs_loaded) return;

      frm.__acefone_logs_loaded = true;
      await reload_call_logs(frm);
    },
  });
});

frappe.realtime.on(CALL_LOG_ADDED_EVENT, function (data) {
  if (!data || !data.call_for_doc || !data.linked_doc) return;

  const current_route = frappe.get_route();
  const [route_type, route_doctype, route_name] = current_route;

  if (
    route_type === "Form" &&
    route_doctype === data.call_for_doc &&
    route_name === data.linked_doc
  ) {
    const frm = frappe.ui.form.get_current();
    if (frm) {
      frm.__acefone_logs_loaded = false;
      reload_call_logs(frm);
      frappe.show_alert({ message: "New call log added", indicator: "green" });
    }
  }
});

async function reload_call_logs(frm) {
  try {
    const response = await frappe.call({
      method:
        "crm_acefone_integration.acefone.doctype.acefone_call_log.acefone_call_log.get_call_logs",
      args: {
        doctype: frm.doctype,
        docname: frm.docname,
      },
    });

    const callLogs = response.message || [];
    if (callLogs.length === 0) return;

    const html = render_call_logs_html(callLogs);

    if (frm.fields_dict[ACEFONE_CALL_LOGS_FIELD]) {
      frm.fields_dict[ACEFONE_CALL_LOGS_FIELD].$wrapper.html(html);
    } else {
      inject_call_log_tab(frm, html);
    }
  } catch (err) {
    console.error("[Acefone] Failed to fetch call logs:", err);
  }
}

function render_call_logs_html(callLogs) {
  let html = `<div class="acefone-call-logs-cards row gy-3">`;

  callLogs.forEach((log) => {
    const type = log.call_type || "";
    const status = log.call_status || "";
    const number = log.customer_phone || log.caller_id || "";
    const start = frappe.datetime.str_to_user(log.start_stamp) || "";
    const duration = log.duration || "0s";
    const recording = log.recording_url
      ? `<a href="${log.recording_url}" target="_blank" class="btn btn-outline-primary btn-sm">Play Recording</a>`
      : `<span class="text-muted">No Recording</span>`;

    const statusBadge =
      status === "Missed"
        ? `<span class="badge bg-danger">${status}</span>`
        : `<span class="badge bg-success">${status}</span>`;

    const typeBadge = `<span class="badge bg-secondary">${type}</span>`;

    html += `
      <div class="col-md-6">
        <div class="card shadow-sm border-0">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
              ${typeBadge} ${statusBadge}
            </div>
            <h6 class="card-title mb-1">📞 ${number}</h6>
            <p class="mb-1 text-muted">🕒 ${start} &nbsp; | &nbsp; ⏱ ${duration}</p>
            <div>${recording}</div>
          </div>
        </div>
      </div>
    `;
  });

  html += `</div>`;
  return html;
}

function inject_call_log_tab(frm, html) {
  const tab_label = "Call Logs";

  let tab = frm.layout.tabs.find((tab) => tab.label === tab_label);
  if (tab) {
    tab.section.$wrapper.empty().append(html);
  } else {
    tab = frm.layout.make_tab({
      label: tab_label,
      fieldtype: "Tab Break",
      fieldname: "acefone_custom_cl_tab",
    });
    frm.layout.make_field({
      fieldname: ACEFONE_CALL_LOGS_FIELD,
      label: "Acefone Call Logs HTML",
      fieldtype: "HTML",
    });
  }

  tab.wrapper
    .find(`[data-fieldname='${ACEFONE_CALL_LOGS_FIELD}']`)
    .append(html);
  tab.toggle(true);
}
