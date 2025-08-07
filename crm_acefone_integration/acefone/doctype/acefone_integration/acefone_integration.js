// Copyright (c) 2025, OneHash and contributors
// For license information, please see license.txt

const phoneFieldsMap = {};

// frappe.ui.form.on("Acefone Integration", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Acefone DocType Subcriptions", {
  subscribed_for: async function (frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    const gridRow = frm.fields_dict.call_subscriptions.grid.get_grid_row(
      row.name,
    );
    const phoneFieldControl = gridRow.columns.phone_field.field;

    if (row.subscribed_for) {
      frappe.model.with_doctype(row.subscribed_for, () => {
        const docMeta = frappe.get_meta(row.subscribed_for);
        const phoneFields = getPhoneFields(docMeta.fields).map((df) => ({
          fieldname: df.fieldname,
          label: df.label,
        }));
        const labels = [];

        for (let field of phoneFields) {
          labels.push(field.label);
          if (!phoneFieldsMap[row.subscribed_for]) {
            phoneFieldsMap[row.subscribed_for] = {};
          }
          phoneFieldsMap[row.subscribed_for][field.label] = field.fieldname;
        }

        phoneFieldControl.df.read_only = 0;
        phoneFieldControl.df.options = labels;
        phoneFieldControl.set_options();
        phoneFieldControl.refresh();
      });
    } else {
      frappe.model.set_value(cdt, cdn, "phone_field", "");
      frappe.model.set_value(cdt, cdn, "phone_fieldname", "");
      phoneFieldControl.df.read_only = 1;
      phoneFieldControl.refresh();
    }
  },
  phone_field: function (frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(
      cdt,
      cdn,
      "phone_fieldname",
      phoneFieldsMap[row.subscribed_for][row.phone_field],
    );
  },
});

function getPhoneFields(docfields) {
  return docfields.filter(
    (df) =>
      (df.fieldtype === "Phone" ||
        (df.fieldtype === "Data" && df.options === "Phone")) &&
      !df.hidden,
  );
}
