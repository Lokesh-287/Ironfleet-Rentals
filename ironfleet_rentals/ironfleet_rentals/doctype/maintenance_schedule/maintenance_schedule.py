# Copyright (c) 2026, IronFleet_Rentals and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe.utils import add_days, today

class MaintenanceSchedule(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        total_parts = sum(row.price * row.qty for row in self.parts_item)
        self.total_parts_cost = total_parts
        self.grand_total_cost = total_parts + self.total_labor_cost

    def on_update_after_submit(self):
        if self.status == "Verified":
            self.complete_maintenance_cycle()

    def complete_maintenance_cycle(self):
        frappe.db.set_value("Equipment", self.equipment, {
        "status": "Available",
            "condition": "Good" if self.maintenance_type == "Corrective" else "Excellent"
        })
        interval =  90
        
        next_date = add_days(today(), interval)
        frappe.db.set_value("Equipment", self.equipment, "next_scheduled_maintenance_date", next_date)
        
        frappe.msgprint(f"Equipment released. Next maintenance scheduled for {next_date}.")