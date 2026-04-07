frappe.ui.form.on("Damage Assessment", {
    refresh: function (frm) {
        check_eligibility(frm);
    },
    estimated_repair_cost: function (frm) {
        check_eligibility(frm);
    },
    severity: function (frm) {
        check_eligibility(frm);
    }
});

var check_eligibility = function (frm) {
    // 1. Remove old buttons so they don't stack or stay when conditions change
    frm.clear_custom_buttons();

    // 2. Button should only show if the document is saved (has a name)
    if (frm.doc.__islocal) return;

    // 3. Check the conditions (Scenario D)
    if (flt(frm.doc.estimated_repair_cost) > 50000 || ["Major", "Critical"].includes(frm.doc.severity)) {

        frm.add_custom_button('File Insurance Claim', () => {
            frappe.call({
                method: "ironfleet_rentals.ironfleet_rentals.api.create_insurance_claim_from_assessment",
                args: { assessment_name: frm.doc.name },
                callback: function (r) {
                    if (r.message && r.message.docname) {
                        if (r.message.status === "exists") {
                            frappe.msgprint("A claim already exists: " + r.message.docname);
                        }
                        frappe.set_route("Form", "Insurance Claim", r.message.docname);
                    }
                }
            });
        }, "Actions"); // Added "Actions" group for better UI
    }
};