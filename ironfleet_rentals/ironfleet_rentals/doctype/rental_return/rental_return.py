import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate

class RentalReturn(Document):
    def validate(self):
        self.calculate_late_fees()
        self.update_total_amount()


    def on_submit(self):
        self.process_returns()
    
    def update_total_amount(self):
        total=0
        for item in self.rental_return_items:
            if item.condition == "Damaged":
                total+=item.damage_charge
        if total:
            self.total_damage_charge=total
            self.total_amount+=self.total_damage_charge


    def calculate_late_fees(self):
        ra = frappe.get_doc("Rental Agreement", self.rental_agreement)
        days_overdue = date_diff(self.return_date, ra.expected_end_date)
        
        if days_overdue > 0:
            penalty_per_item = frappe.db.get_single_value("Rental Settings", "late_fee_per_day") or 0
            total_daily_rate = 0
            
            for item in self.rental_return_items:
                if item.equipment_id:
                    rate = frappe.db.get_value("Equipment", item.equipment_id, "default_daily_rental_rate")
                    total_daily_rate += flt(rate)
            
            penalty_total = flt(penalty_per_item) * len(self.rental_return_items)
            self.late_fees = (total_daily_rate + penalty_total) * days_overdue
        else:
            self.late_fees = 0

    def process_returns(self):
        for item in self.rental_return_items:
            if not item.equipment_id: continue
            
            # Logic: If Damaged -> Under Maintenance, Else -> Available
            if item.condition == "Damaged":
                frappe.db.set_value("Equipment", item.equipment_id, {
                    "status": "Under Maintenance",
                    "condition": "Damaged" 
                })
                self.create_maintenance_entry(item)
            else:
                frappe.db.set_value("Equipment", item.equipment_id, {
                    "status": "Available",
                    "condition": item.condition 
                })
        
        frappe.db.set_value("Rental Agreement", self.rental_agreement, "status", "Completed")

    def create_maintenance_entry(self, item):
        maint = frappe.get_doc({
            "doctype": "Maintenance Schedule",
            "equipment": item.equipment_id,
            "maintenance_type": "Corrective",
            "status": "Scheduled",
            "scheduled_date": self.return_date,
            "rental_return": self.name,
            "description": f"Damaged during rental {self.rental_agreement}. Notes: {item.damage_description}"
        })
        maint.insert(ignore_permissions=True)