frappe.ui.form.on("Maintenance Schedule", {
    total_labor_cost: function (frm) {
        calculate_grand_total(frm);
    },

    parts_item_remove: function (frm) {
        calculate_parts_total(frm);
    },
    refresh: function (frm) {
        if (frm.doc.docstatus === 0) {
            if (frm.doc.status === "Scheduled" && frm.doc.technician) {
                frm.add_custom_button('Assign Task', () => {
                    frm.set_value("status", "Assigned");
                    frm.save();
                });
            }
            if (frm.doc.status === "Assigned") {
                frm.add_custom_button('Start Work', () => {
                    frm.set_value("status", "In Progress");
                    frm.save();
                });
            }

            if (frm.doc.status === "In Progress") {
                frm.add_custom_button('Mark Completed', () => {
                    frm.set_value("status", "Completed");
                    frm.save().then(() => {
                        frappe.msgprint("Work finished. Please Submit the document for Verification.");
                    });
                });
            }
        }
        if (frm.doc.docstatus === 1 && frm.doc.status === "Completed") {
            frm.add_custom_button('Verify & Release', () => {
                frm.set_value("status", "Verified");
                frm.save();
            }, "Actions");
        }
    }
});

frappe.ui.form.on("Maintenance Part Items", {
    price: function (frm, cdt, cdn) {
        calculate_parts_total(frm);
    },
    qty: function (frm, cdt, cdn) {
        calculate_parts_total(frm);
    }
});

var calculate_parts_total = function (frm) {
    let total_parts = 0;

    (frm.doc.parts_item || []).forEach(row => {
        total_parts += (row.price * row.qty);
    });

    frm.set_value("total_parts_cost", total_parts);
    calculate_grand_total(frm);
};

var calculate_grand_total = function (frm) {
    let grand_total = frm.doc.total_parts_cost + frm.doc.total_labor_cost
    frm.set_value("grand_total_cost", grand_total);
};