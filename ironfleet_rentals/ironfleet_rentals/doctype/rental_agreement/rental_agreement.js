// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rental Agreement", {
	refresh(frm) {

	},
    setup(frm){
        frm.set_query("equipment_categorys","items",function(doc,cdt,cdn){
            return{
                query:"ironfleet_rentals.ironfleet_rentals.api.get_leaf_nodes_parent"
            }
        })
    }
});

frappe.ui.form.on("Rental Agreement Items",{
    equipment_categorys:function(frm,cdt,cdn){
        let row=locals[cdt][cdn]
        frappe.call({
            method :"ironfleet_rentals.ironfleet_rentals.api.get_daily_rate",
            args:{
                equipment_category : row.equipment_categorys
            },
            callback:function(r){
                if (r.message){
                    row.daily_rate=r.message
                    row.qty=1
                    row.total=r.message
                }
            }
        })
    },
    qty:function(frm,cdt,cdn){
        let row=locals[cdt][cdn]
        row.total=row.daily_rate*row.qty
    }
})

// frappe.call({
// 				method: "frappe.automation.doctype.auto_repeat.auto_repeat.generate_message_preview",
// 				type: "POST",
// 				args: {
// 					name: frm.doc.name,
// 				},
// 				callback: function (r) {
// 					if (r.message) {
// 						frappe.msgprint(r.message.message, r.message.subject);
// 					}
// 				},
// 			}
