// Copyright (c) 2026, IronFleet_Rentals and contributors
// For license information, please see license.txt

frappe.ui.form.on("Equipment", {
	refresh(frm) {
        const todaydate=frappe.datetime.get_today()
        const date_diff=frappe.datetime.get_day_diff( frm.doc.next_scheduled_maintenance_date , todaydate)
        frm.dashboard.indicators=[]
        if (date_diff < 0){
            frm.dashboard.add_indicator( `Manitenance scheduled Expried`,"red")
        }
        else if (date_diff <= 7){
            frm.dashboard.add_indicator( `Manitenance scheduled Due in ${date_diff}`,"yellow")
        }
        ress_date_diff=frappe.datetime.get_day_diff( frm.doc.registration_expired_date , todaydate)
        
        if (ress_date_diff <= 0){
            frm.dashboard.add_indicator( `Registration scheduled Expried`,"red")
            console.log(ress_date_diff)
        }
	},
    setup:function(frm){
        frm.set_query("equipment_catgory",()=>{
            return{
                filters:{
                    is_group:0
                }
            }
        })
    }
});
