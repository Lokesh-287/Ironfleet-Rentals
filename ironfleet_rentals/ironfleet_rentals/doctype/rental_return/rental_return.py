import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate

class RentalReturn(Document):
    def validate(self):
        self.calculate_late_fees()
        self.calculate_billing()
        self.update_total_amount()


    def on_submit(self):
        self.process_returns()

    def calculate_billing(self):        
        is_interrupted = frappe.db.get_value("Rental Agreement", self.rental_agreement, "service_interruption")        
        ra = frappe.get_doc("Rental Agreement", self.rental_agreement)
        total_days = date_diff(self.return_date, ra.from_date)
        if is_interrupted:
            total_days = max(0, total_days - 1)
            frappe.msgprint(f"Service Interruption detected on Agreement.")
        daily_rate_sum = 0
        for item in ra.rental_agreement_items:
            daily_rate_sum += flt(item.daily_rate)
        self.balance = total_days * daily_rate_sum
    
    def update_total_amount(self):
        total=0
        for item in self.rental_return_items:
            if item.condition == "Damaged":
                total+=item.damage_charge
        if total:
            self.total_damage_charge=total
            self.total_amount=self.total_damage_charge + self.balance


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
                self.create_damage_assessment(item)
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

    def create_damage_assessment(self, item):
        assessment = frappe.get_doc({
            "doctype": "Damage Assessment",
            "equipment": item.equipment_id,
            "rental_return": self.name,
            "severity": item.severity,
            "estimated_repair_cost": flt(item.damage_charge),
            "is_covered_by_insurance": item.insurance_covered,
            "notes": item.damage_description,
        })
        assessment.insert(ignore_permissions=True)