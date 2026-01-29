const CALL_LOG_ADDED_EVENT = "acefone_call_log_added";
const ACEFONE_CALL_LOGS_FIELD = "acefone_call_logs_html";
const ACEFONE_TAB_CALL_LOGS_FIELD = "acefone_tab_call_logs_html";
const ACEFONE_CALL_LOG_TAB_LABEL = "Call Logs";

const acefone_hooked_doctypes = new Set();
$(document).on("form-refresh", function (_, frm) {
  if (!frm || !frm.doctype) return;
  if (acefone_hooked_doctypes.has(frm.doctype)) return;

  acefone_hooked_doctypes.add(frm.doctype);
  frappe.ui.form.on(frm.doctype, {
    refresh(frm) {
      reload_call_logs(frm);
    },
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
      const frm = cur_frm;
      if (frm) {
        reload_call_logs(frm).then(() => {
          frappe.show_alert({
            message: "New call log added",
            indicator: "green",
          });
        });
      }
    }
  });
});

async function reload_call_logs(frm) {
  try {
    reset_call_log_ui(frm);
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
  let html = `<div class="acefone-call-logs-list">
  <style>
  .acefone-call-logs-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .call-log-card {
    transition: box-shadow 0.2s ease;
    border-radius: 0.75rem;
    border: 1px solid #f1f3f5;
  }
  .call-log-card:hover {
    box-shadow: 0 0.5rem 1.25rem rgba(0, 0, 0, 0.08);
  }
  .call-log-card .badge {
    font-size: 0.75rem;
    padding: 0.35em 0.6em;
    border-radius: 0.4rem;
  }
  .agent-info {
    font-size: 0.875rem;
    color: #495057;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .agent-info i {
    color: #0d6efd;
  }
  .call-note {
    background: #f8f9fa;
    border-left: 3px solid #0d6efd;
    border-radius: 0.4rem;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
    color: #212529;
    margin-top: 0.75rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .call-note i {
    color: #0d6efd;
    margin-top: 0.32rem;
  }
  .view-log-link {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.85rem;
    color: #0d6efd;
    text-decoration: none;
    font-weight: 500;
    margin-top: 0.75rem;
    transition: color 0.15s ease;
  }
  .view-log-link:hover {
    color: #084298;
    text-decoration: underline;
  }
  </style>`;

  callLogs.forEach((log) => {
    const type = log.call_type || "";
    const status = log.call_status || "";
    const number = log.customer_phone || log.caller_id || "";
    const start = frappe.datetime.str_to_user(log.start_stamp) || "";
    const duration = log.duration || "0s";
    const callNote = log.call_note || "";
    const agentName = log.agent_name || "Unknown Agent";
    const callLogLink = frappe.utils.get_form_link(
      "Acefone Call Log",
      log.name,
    );

    const recording = log.recording_url
      ? `<button data-url="${log.recording_url}" class="btn btn-outline-primary btn-sm acefone_play_btn">
          <i class="fa fa-play-circle-o me-1"></i> Play Recording
         </button>`
      : `<span class="text-muted small">No Recording</span>`;

    const statusBadge =
      status === "Missed"
        ? `<span class="badge bg-danger-subtle text-danger border border-danger-subtle">${status}</span>`
        : `<span class="badge bg-success-subtle text-success border border-success-subtle">${status}</span>`;

    const typeBadge = `<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle">${type}</span>`;

    html += `
      <div class="card call-log-card mb-3 shadow-sm border-0">
        <div class="card-body">
          <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-3">
            <div class="mb-2 mb-md-0">
              <div class="agent-info mb-2">
                <i class="fa fa-user-circle"></i> ${agentName}
              </div>
              <h5 class="mb-1 text-primary">
                <i class="fa fa-phone me-2"></i> ${number}
              </h5>
              <div class="text-muted small mb-1">
                <i class="fa fa-clock me-1"></i> ${start}
                &nbsp;|&nbsp;
                <i class="fa fa-hourglass-half me-1"></i> ${duration}
              </div>
              <div class="d-flex flex-wrap gap-2 mt-2">
                ${typeBadge}
                ${statusBadge}
              </div>
            </div>
            <div>
              ${recording}
            </div>
          </div>

          ${
            callNote
              ? `<div class="call-note">
                  <i class="fa fa-sticky-note"></i>
                  <div>${callNote}</div>
                </div>`
              : ""
          }

          <a href="${callLogLink}" class="view-log-link" target="_blank">
            <i class="fa fa-external-link"></i> View Full Call Log
          </a>
        </div>
      </div>
    `;
  });

  html += `</div>`;
  return html;
}

function inject_call_log_tab(frm, html) {
  let tab = frm.layout.tabs.find(
    (tab) => tab.label === ACEFONE_CALL_LOG_TAB_LABEL,
  );
  if (!tab) {
    tab = frm.layout.make_tab({
      label: ACEFONE_CALL_LOG_TAB_LABEL,
      fieldtype: "Tab Break",
      fieldname: "acefone_custom_cl_tab",
    });
    frm.layout.make_field({
      fieldname: ACEFONE_TAB_CALL_LOGS_FIELD,
      label: "Acefone Call Logs HTML",
      fieldtype: "HTML",
    });
  }

  tab.wrapper
    .find(`[data-fieldname='${ACEFONE_TAB_CALL_LOGS_FIELD}']`)
    .empty()
    .append(html);

  tab.wrapper.off("click", handleCallLogsClick);
  tab.wrapper.on("click", handleCallLogsClick);

  tab.toggle(true);
  tab.show();
}

function handleCallLogsClick(e) {
  const playBtn = e.target.closest(".acefone_play_btn");
  if (playBtn) {
    playAudioPopup(playBtn.dataset.url);
  }
}

function reset_call_log_ui(frm) {
  if (frm.fields_dict[ACEFONE_CALL_LOGS_FIELD]) {
    frm.fields_dict[ACEFONE_CALL_LOGS_FIELD].$wrapper.empty();
  } else {
    remove_call_log_tab(frm);
  }
}

function remove_call_log_tab(frm) {
  let tab = frm.layout.tabs.find(
    (tab) => tab.label === ACEFONE_CALL_LOG_TAB_LABEL,
  );
  if (tab) {
    frm.fields_dict[ACEFONE_TAB_CALL_LOGS_FIELD].$wrapper.empty();
    tab.hide();
  }
}

function playAudioPopup(audioUrl) {
  if (!audioUrl) {
    frappe.msgprint(__("No audio URL found in the document."));
    return;
  }

  const audio_html = `
        <audio controls autoplay style="width: 100%;">
            <source src="${audioUrl}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
    `;

  frappe.msgprint({
    title: __("Audio Player"),
    indicator: "blue",
    message: audio_html,
    wide: true,
  });
}
