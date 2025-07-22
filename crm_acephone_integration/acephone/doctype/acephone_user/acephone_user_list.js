const DIALOG_TITLE = "Syncing Acephone Users";

frappe.listview_settings["Acephone User"] = {
  onload: function (listview) {
    listview.page.add_inner_button("Sync Acephone Users", function () {
      frappe.call({
        method:
          "crm_acephone_integration.acephone.doctype.acephone_user.acephone_user.sync_acephone_users",
        callback: function (response) {
          if (response && response.message) {
            if (response.message.status === "success") {
              frappe.show_alert(
                response.message.msg || "Acephone Users syncing started.",
              );
              frappe.realtime.on(response.message.track_on, (msg) => {
                progressDialog = frappe.show_progress(
                  msg.title || DIALOG_TITLE,
                  msg.progress,
                  msg.total,
                  "Please Wait...",
                  true,
                );
              });
            } else {
              frappe.throw(
                `Error occured during syncing users: ${response.message}`,
              );
            }
          }
        },
      });
    });
  },
};
