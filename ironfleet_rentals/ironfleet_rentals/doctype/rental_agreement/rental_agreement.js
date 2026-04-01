// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rental Agreement", {
    refresh(frm) {
        console.log(frm.doc.docstatus);

        if (frm.doc.docstatus === 0) {
            frm.trigger("load_security_deposit_percentage");
            frm.trigger("recalculate_totals");
        }

        if (frm.doc.docstatus === 1 && frm.doc.status !== "Completed") {
            frm.add_custom_button('Create Return', function () {
                frappe.call({
                    method: "ironfleet_rentals.ironfleet_rentals.api.make_rental_return",
                    args: {
                        rental_agreement: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            // Redirect to the newly created Return document
                            frappe.set_route("Form", "Rental Return", r.message);
                        }
                    }
                });
            });
        }

        if (frm.doc.docstatus === 1 && frm.doc.out_standing_amount > 0) {
            frm.add_custom_button(__('Record Payment'), function () {
                let d = new frappe.ui.Dialog({
                    title: __('Capture Payment'),
                    fields: [
                        {
                            label: __('Select Installment'),
                            fieldname: 'row_id',
                            fieldtype: 'Select',
                            options: frm.doc.payment_schedule
                                .filter(row => row.status !== 'Paid')
                                .map(row => ({ label: `${row.payment_term} (${format_currency(row.amount)})`, value: row.name })),
                            reqd: 1
                        },
                        {
                            label: __('Payment Mode'),
                            fieldname: 'mode',
                            fieldtype: 'Select',
                            options: ["Cash", "UPI", "Bank Transfer", "Card", "Cheque"],
                            reqd: 1
                        },
                        {
                            label: __('Reference Number'),
                            fieldname: 'ref',
                            fieldtype: 'Data',
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Submit Payment'),
                    primary_action(values) {
                        frappe.call({
                            method: "ironfleet_rentals.ironfleet_rentals.api.capture_rental_payment",
                            args: {
                                rental_agreement: frm.doc.name,
                                row_id: values.row_id,
                                reference_no: values.ref,
                                payment_mode: values.mode
                            },
                            callback: function (r) {
                                d.hide();
                                frm.reload_doc();
                                frappe.show_alert({ message: __('Payment Successful. Remaining: ') + format_currency(r.message), indicator: 'green' });
                            }
                        });
                    }
                });
                d.show();
            });
        }

        // Only show button if Agreement is in Draft
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(("Create Sourcing Request"), function () {
                frappe.call({
                    method: "ironfleet_rentals.ironfleet_rentals.api.create_sourcing_request",
                    args: {
                        rental_agreement: frm.doc.name,
                        items: frm.doc.items
                    },
                    freeze: true,
                    freeze_message: ("Checking Stock & Vendors..."),
                    callback: function (r) {

                        if (!r.message) return;

                        const res = r.message;

                        // CASE 1: Missing Vendors - Redirect to New Vendor Form
                        if (res.status === "missing_vendor") {
                            frappe.confirm(
                                ("No Subcontractors found for: <b>{0}</b>. Create a new Vendor now?", [res.categories.join(", ")]),
                                function () {
                                    console.log("DEBUG: Creating Vendor via Server...");

                                    frappe.call({
                                        method: "ironfleet_rentals.ironfleet_rentals.api.quick_create_vendor",
                                        args: {
                                            categories: res.categories
                                        },
                                        callback: function (r) {
                                            if (r.message) {
                                                frappe.show_alert({
                                                    message: ("Vendor {0} created successfully", [r.message]),
                                                    indicator: 'green'
                                                });

                                                // Route to the newly created Vendor so user can fill in phone/email
                                                frappe.set_route("Form", "Vendor", r.message);
                                            }
                                        }
                                    });
                                },
                                function () {
                                    frappe.msgprint(("Sourcing terminated."));
                                }
                            );
                        }
                        // CASE 2: Success - Redirect to Sourcing Doc
                        else if (res.status === "success") {
                            frappe.show_alert({ message: ("Sourcing Created"), indicator: 'green' });
                            frappe.set_route("Form", "Subcontract Sourcing", res.docname);
                        }
                        // CASE 3: No gaps found
                        else if (res.status === "none") {
                            frappe.msgprint(res.message);
                        }
                    }
                });
            });
        }
    },

    setup(frm) {
        frm.set_query("equipment_categorys", "items", function () {
            return {
                query: "ironfleet_rentals.ironfleet_rentals.api.get_leaf_nodes",
            };
        });
    },

    start_date(frm) { frm.trigger("recalculate_totals"); },
    expected_end_date(frm) { frm.trigger("recalculate_totals"); },
    discount_percentage(frm) { frm.trigger("recalculate_totals"); },
    items_remove(frm) { frm.trigger("recalculate_totals"); },

    load_security_deposit_percentage(frm) {
        if (frm.security_deposit_percentage !== undefined) return;
        frappe.db.get_single_value("Rental Settings", "security_deposit_percentage").then((value) => {
            frm.security_deposit_percentage = value;
            frm.trigger("recalculate_totals");
        });
    },

    recalculate_totals(frm) {
        if (frm.doc.docstatus > 0) return;
        let totalDailyRate = 0;
        (frm.doc.items || []).forEach((item) => {
            const qty = item.qty || 1;
            const dailyRate = item.daily_rate || 0;
            const total = dailyRate * qty;
            if (item.total !== total) {
                frappe.model.set_value(item.doctype, item.name, "total", total);
            }
            totalDailyRate += total;
        });

        let rentalDays = 0;
        if (frm.doc.start_date && frm.doc.expected_end_date) {
            rentalDays = frappe.datetime.get_day_diff(frm.doc.expected_end_date, frm.doc.start_date) + 1;
            rentalDays = Math.max(rentalDays, 0);
        }

        const estimatedTotal = totalDailyRate * rentalDays;
        const discountAmount = estimatedTotal * (frm.doc.discount_percentage || 0) / 100;
        const netRentalTotal = estimatedTotal - discountAmount;
        const securityDeposit = netRentalTotal * (frm.security_deposit_percentage || 0) / 100;

        frm.set_value("total_daily_rate", totalDailyRate);
        frm.set_value("estimate_rental_days", rentalDays);
        frm.set_value("estimated_total", estimatedTotal);
        frm.set_value("discount_amount", discountAmount);
        frm.set_value("security_deposit", securityDeposit);
        frm.set_value("grand_total", netRentalTotal + securityDeposit);
    },
});

frappe.ui.form.on("Rental Agreement Items", {
    equipment_categorys(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.equipment_categorys) return;

        frappe.call({
            method: "ironfleet_rentals.ironfleet_rentals.api.get_daily_rate",
            args: { equipment_category: row.equipment_categorys },
            callback: function (r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, "daily_rate", flt(r.message));
                    frappe.model.set_value(cdt, cdn, "qty", flt(row.qty) || 1);
                    frm.trigger("recalculate_totals");
                }
            },
        });
    },
    qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "total", flt(row.daily_rate) * (flt(row.qty) || 1));
        frm.trigger("recalculate_totals");
    },
    daily_rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "total", flt(row.daily_rate) * (flt(row.qty) || 1));
        frm.trigger("recalculate_totals");
    },
});