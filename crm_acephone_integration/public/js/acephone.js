frappe.provide("frappe.acephone");

frappe.acephone.CallPopupHandler = class CallPopupHandler {
  constructor() {
    this.bindEvents();
  }

  bindEvents() {
    frappe.realtime.on("agent_answered_call", (data) => {
      this.showCallPopup(data);
    });
  }

  showCallPopup(data) {
    const quickEntryDialog = frappe.ui.form.make_quick_entry(
      "Acephone Call Note",
      null,
      () => {
        console.log("Make Note");
      },
      data,
      true,
    );
  }
};

$(document).ready(function () {
  if (!window.acephone_call_popup) {
    window.acephone_call_popup = new frappe.acephone.CallPopupHandler();
  }
});
