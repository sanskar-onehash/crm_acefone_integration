frappe.provide("frappe.acephone");

frappe.acephone.CallPopupHandler = class CallPopupHandler {
  static NOTE_DOCTYPE = "Acephone Call Note";
  static REALTIME_EVENT_ID = "agent_answered_call";

  constructor() {
    this.data = null;
    this.control = null;
    this.bindEvents();
  }

  bindEvents() {
    frappe.realtime.on(
      frappe.acephone.CallPopupHandler.REALTIME_EVENT_ID,
      (data) => {
        this.data = {
          doctype: frappe.acephone.CallPopupHandler.NOTE_DOCTYPE,
          ...data,
        };
        this.showCallPopup();
      },
    );
  }

  async showCallPopup(minimized = false) {
    this.control = await frappe.ui.form.make_quick_entry(
      frappe.acephone.CallPopupHandler.NOTE_DOCTYPE,
      null,
      null,
      this.data,
      true,
    );
    const $minimizeBtn = this.control.dialog.get_minimize_btn();
    $minimizeBtn.removeClass("hide");
    $minimizeBtn.click(() => this.toggleMinimize());

    if (minimized) {
      this.control.dialog.toggle_minimize();
    }

    this.control.dialog.add_custom_action(
      "View Linked Doc",
      () => this.handleViewDoc(),
      "btn-primary",
    );
    this.control.dialog.add_custom_action(
      "Minimize",
      () => this.toggleMinimize(),
      "btn-primary ml-2",
    );
  }

  async handleViewDoc() {
    const doctype = this.control.dialog.get_value("note_for");
    const docname = this.control.dialog.get_value("linked_doc");

    if (doctype && docname) {
      await frappe.set_route("Form", doctype, docname);
      this.control.dialog.cancel();
      this.showCallPopup(true);
    } else {
      frappe.throw("Note For & Linked Doc are required to view doc.");
    }
  }

  toggleMinimize() {
    this.control.dialog.toggle_minimize();
  }
};

$(document).ready(function () {
  if (!window.acephone_call_popup) {
    window.acephone_call_popup = new frappe.acephone.CallPopupHandler();
  }
});
