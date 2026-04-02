frappe.ui.form.on("Insurance Claim", {
    refresh: function (frm) {
        frm.clear_custom_buttons();

        if (frm.doc.status === "Filed") {
            frm.add_custom_button('Start Review', () => {
                frm.set_value("status", "Under Review");
                frm.save();
            });
        }
        if (frm.doc.status === "Under Review") {
            frm.add_custom_button('Assign Surveyor', () => {
                frm.set_value("status", "Surveyor Assigned");
                frm.save();
            });
        }
        if (frm.doc.status === "Surveyor Assigned") {
            frm.add_custom_button('Approve Claim', () => {
                frm.set_value("status", "Approved");
                frm.save();
            }, "Actions");

            frm.add_custom_button('Reject Claim', () => {
                frm.set_value("status", "Rejected");
                frm.save();
            }, "Actions");
        } if (frm.doc.status === "Approved") {
            frm.add_custom_button('Mark as Settled', () => {
                if (!frm.doc.settlement_amount) {
                    frappe.msgprint("Please enter the Settlement Amount first.");
                    return;
                }
                frm.set_value("status", "Settled");
                frm.save();
            });
        }
    }
});