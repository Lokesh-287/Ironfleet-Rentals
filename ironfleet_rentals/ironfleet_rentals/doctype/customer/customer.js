// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer", {
	refresh(frm) {
		if (frm.doc.outstanding_payment > frm.doc.credit_limit) {
			frm.dashboard.set_headline_alert("Outstanding Payment Exceeded Credit Limit", "red");
		} else {
			frm.dashboard.clear_headline();
		}
	},
});
