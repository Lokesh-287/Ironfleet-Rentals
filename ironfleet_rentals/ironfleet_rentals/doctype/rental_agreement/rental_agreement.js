// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rental Agreement", {
    refresh(frm) {
        console.log("DEBUG: Form Refresh Triggered");

        frm.trigger("load_security_deposit_percentage");
        frm.trigger("recalculate_totals");

        // Only show button if Agreement is in Draft
        if (frm.doc.docstatus === 0) {
            console.log("DEBUG: Adding Sourcing Button");
            frm.add_custom_button(("Create Sourcing Request"), function () {
                
                console.log("DEBUG: Sourcing Button Clicked");

                frappe.call({
                    method: "ironfleet_rentals.ironfleet_rentals.api.create_sourcing_request",
                    args: {
                        rental_agreement: frm.doc.name,
                        items: frm.doc.items
                    },
                    freeze: true,
                    freeze_message: ("Checking Stock & Vendors..."),
                    callback: function (r) {
                        console.log("DEBUG: Server Response ->", r);

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
                callback: function(r) {
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
                            console.info("DEBUG: Status NONE ->", res.message);
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