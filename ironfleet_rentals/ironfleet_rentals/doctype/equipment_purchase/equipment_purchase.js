// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Equipment Purchase", {
	refresh(frm) {
        if(frm.doc.status  === "Ordered"){
            frm.add_custom_button(
                "Receive Equipment",function(){
                    frappe.confirm("Are you sure you received the equipment?", function () {
                        frappe.call({
                    method: "ironfleet_rentals.ironfleet_rentals.api.create_equipment_records",
                    args: {
                        equipment_category: frm.doc.equipment_category,
                        qty: frm.doc.qty,
                        vendor:frm.doc.vendor,
                        purchase_date:frm.doc.purchase_date,
                        default_rate:frm.doc.rate
                    },
                    callback: function (r) {
                        frm.set_value("status", "Received");
                        frm.save("Submit").then(() => {
                            frappe.msgprint("Equipment Received & Records Created");
                            frm.reload_doc();
                        });
                    }
                });
                    })
                }
            )
        }
	},
    vendor:function(frm){
        frm.set_value('equipment_category', '');
        frm.set_query('equipment_category', function() {
            return {
                query: "ironfleet_rentals.ironfleet_rentals.api.get_vendor_equipment_categorys",
                filters: {
                    "vendor":frm.doc.vendor
                }
            };
        });
    },
    equipment_category:function(frm){
        if (!frm.doc.equipment_category) {
        return;
    }
        frappe.call({
			method: "ironfleet_rentals.ironfleet_rentals.api.get_daily_rate",
			args: {
				equipment_category: frm.doc.equipment_category,
			},
			callback: function (r) {
				if (r.message) {
					frm.doc.rate=r.message
                    frm.refresh_field("rate");
					frm.doc.qty= frm.doc.qty || 1
                    frm.refresh_field("qty");
                    frm.doc.total_amount = frm.doc.qty * frm.doc.rate
                    frm.refresh_field("total_amount");
                }
			},
		});
    },
    qty:function(frm){
        if(frm.doc.qty && frm.doc.rate)
        frm.doc.total_amount = frm.doc.qty * frm.doc.rate
        frm.refresh_field("total_amount");
    }
    
});
