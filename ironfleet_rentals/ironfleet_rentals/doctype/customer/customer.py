# Copyright (c) 2026, IronFleet_Rentals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Customer(Document):
	def validate(self):
		if not self.mobile_no:
			frappe.msgprint("Note: Mobile number is recommended for real-time Emergency Service updates.")
