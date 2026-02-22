// Copyright (c) 2025, Hex Flow and contributors
// For license information, please see license.txt

frappe.ui.form.on("Face Attendance Settings", {
    refresh: function(frm) {
        if (!frm.doc.description) {
                    frm.set_intro("You must uncheck the 'Create user permission' ", 'red');
                }},
    train_images: function(frm) {
        frappe.warn('Are you sure you want to proceed?',
                    'It will take some time to process and train the model with current employee images.',
                    () => {
                         frappe.call({
                            method: "hex_face.utils.training.sync_employee_images",
                            args: {
                                model: frm.doc.model || "hog"
                            },
                            freeze: true,
                            freeze_message: __("Training face data..."),
                            callback: function(r) {
                                if (!r.exc) {
                                    if (r.message && r.message.status === "success") {
                                        frappe.msgprint(__("Training completed. Encodings saved at: " + r.message.path));
                                    } else {
                                        frappe.msgprint(__("Training failed: " + (r.message.reason || "Unknown error")));
                                    }
                                }
                            }
                        });
                    },
                    'Continue',
                    true // Sets dialog as minimizable
                )



       
    }
});
