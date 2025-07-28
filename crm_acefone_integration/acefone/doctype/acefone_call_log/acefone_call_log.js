// Copyright (c) 2025, OneHash and contributors
// For license information, please see license.txt

frappe.ui.form.on("Acefone Call Log", {
  refresh(frm) {
    addCallLogsActions(frm);
  },
});

function addCallLogsActions(frm) {
  if (!frm.is_new()) {
    addPlayRecordingBtn(frm);
  }
}

function addPlayRecordingBtn(frm) {
  if (!frm.doc.recording_url) {
    return;
  }
  const BTN_LABEL = "Play Recording";
  frm.page.remove_inner_btn(BTN_LABEL);
  frm.page.add_inner_btn(
    BTN_LABEL,
    () => playAudioPopup(frm.doc.recording_url),
    null,
    "primary",
  );
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
