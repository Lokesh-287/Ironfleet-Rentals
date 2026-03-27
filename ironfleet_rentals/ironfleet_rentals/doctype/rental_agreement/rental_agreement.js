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
