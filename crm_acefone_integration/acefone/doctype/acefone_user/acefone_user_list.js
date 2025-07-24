const DIALOG_TITLE = "Syncing Acefone Users";

frappe.listview_settings["Acefone User"] = {
  onload: function (listview) {
    listview.page.add_inner_button("Sync Acefone Users", function () {
      frappe.call({
        method:
          "crm_acefone_integration.acefone.doctype.acefone_user.acefone_user.sync_acefone_users",
        callback: function (response) {
          if (response && response.message) {
            if (response.message.status === "success") {
              frappe.show_alert(
                response.message.msg || "Acefone Users syncing started.",
                5,
              );
              frappe.realtime.on(response.message.track_on, (msg) => {
                progressDialog = frappe.show_progress(
                  msg.title || DIALOG_TITLE,
                  msg.progress,
                  msg.total,
                  "Please Wait...",
                  true,
                );
                if (msg.progress === msg.total) {
                  frappe.show_alert(
                    {
                      indicator: "green",
                      message: "Acefone Users synced successfully.",
                    },
                    5,
                  );
                }
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
