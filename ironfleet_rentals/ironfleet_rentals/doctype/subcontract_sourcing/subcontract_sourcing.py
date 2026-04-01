# Copyright (c) 2026, IronFleet_Rentals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SubcontractSourcing(Document):
	
    def before_insert(self):
        if frappe.db.exists("Subcontract Sourcing",{"rental_agreement":self.rental_agreement}):
            frappe.throw("You cant able to create 2 Subcontract Sourcing For same rental agreement")