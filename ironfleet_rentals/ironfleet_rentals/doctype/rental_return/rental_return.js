// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rental Return", {
    refresh(frm) {
        if (frm.doc.total_amount && frm.doc.is_fully_paid != 1) {
            ~frm.add_custom_button("Make Final Payment", () => {
                let d = new frappe.ui.Dialog({
                    title: "Capture Payment",
                    fields: [
                        {
                            label: "Total Amount",
                            fieldname: "amount",
                            fieldtype: "Currency",
                            default: frm.doc.total_amount,
                            read_only: 1
                        },
                        {
                            label: "Payment Mode",
                            fieldname: "mode",
                            fieldtype: "Select",
                            options: ["Cash", "UPI", "Bank Transfer", "Card", "Cheque"],
                            reqd: 1
                        }
                    ],
                    primary_action_lable: "Submit Payment",
                    primary_action(values) {
                        frappe.call({
                            method: "ironfleet_rentals.ironfleet_rentals.api.make_final_payment",
                            args: {
                                rental_agreement: frm.doc.rental_agreement,
                                rental_return: frm.doc.name,
                                payment_mode: values.mode
                            },
                            callback: function (r) {
                                d.hide();
                                frm.reload_doc();
                                frappe.show_alert({ message: ('Payment Successful'), indicator: 'green' });
                            }
                        });
                    }
                });
                d.show();
            })
        }
    },
});
