import frappe
from frappe.model.document import Document
from frappe.utils import flt

class InsuranceClaim(Document):
    def validate(self):
        self.calculate_net_cost()

    def calculate_net_cost(self):
        repair_cost = frappe.db.get_value("Damage Assessment", 
            self.damage_assessment, "estimated_repair_cost") or 0
        
        self.net_repair_cost = flt(repair_cost) - flt(self.settlement_amount)

    def on_update(self):
        if self.status == "Settled" and not self.settlement_amount:
            frappe.throw("You cannot settle a claim without entering the Settlement Amount.")
        
        if self.status == "Rejected":
            frappe.msgprint("Claim Rejected. Total repair cost will be borne by the company.")