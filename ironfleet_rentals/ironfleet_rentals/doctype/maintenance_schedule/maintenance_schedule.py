import frappe
from frappe.model.document import Document
from frappe.utils import add_days, today, flt 

class MaintenanceSchedule(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        total_parts = 0
        for row in self.get("parts_item"):
            total_parts += flt(row.price) * flt(row.qty)
        self.total_parts_cost = total_parts
        self.grand_total_cost = flt(total_parts) + flt(self.total_labor_cost)

    def on_update_after_submit(self):
        if self.status == "Verified":
            self.complete_maintenance_cycle()
    
    def on_submit(self):
        if self.maintenance_type == "Emergency":
            agreement = frappe.db.get_value("Rental Agreement Item", 
            {"equipment_id": self.equipment, "docstatus": 1}, "parent")
        
            if agreement:
                frappe.db.set_value("Rental Agreement", agreement, "service_interruption", 1)
                frappe.msgprint("Emergency Breakdown: Billing paused for Agreement " + agreement)

    def complete_maintenance_cycle(self):
        if not self.equipment:
            return
            
        frappe.db.set_value("Equipment", self.equipment, {
            "status": "Available",
            "condition": "Good" if self.maintenance_type == "Corrective" else "Excellent"
        })
        
        interval = 90
        next_date = add_days(today(), interval)
        frappe.db.set_value("Equipment", self.equipment, "next_scheduled_maintenance_date", next_date)
        
        frappe.msgprint("Equipment " + self.equipment + " released. Next maintenance scheduled for " + next_date)