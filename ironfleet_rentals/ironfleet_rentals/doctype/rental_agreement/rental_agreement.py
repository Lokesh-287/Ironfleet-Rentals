# Copyright (c) 2026, IronFleet_Rentals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate

from ironfleet_rentals.ironfleet_rentals.api import get_daily_rate


class RentalAgreement(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_totals()
	
	def on_submit(self):
				self.validate_and_assign_equipment()
			
	def validate_and_assign_equipment(self):
        self.set("equipment_list", [])
        
        # Ensure dates are in date format for comparison
        start = getdate(self.start_date)
        end = getdate(self.expected_end_date)

        for item in self.items:
            category = item.equipment_categorys
            required_qty = int(item.qty)

            # Advanced Query: Filter by Category, Status, and Expiry Dates
            # Sort by Vendor Performance Rating descending
            available_ids = frappe.db.sql("""
                SELECT 
                    e.name 
                FROM 
                    `tabEquipment` e
                LEFT JOIN 
                    `tabVendor` v ON e.vendor = v.name
                WHERE 
                    e.equipment_catgory = %s 
                    AND e.status = 'Available'
                    AND (e.insurance_expired_date IS NULL OR e.insurance_expired_date > %s)
                    AND (e.registration_expired_date IS NULL OR e.registration_expired_date > %s)
                    AND (e.next_scheduled_maintenance_date IS NULL OR e.next_scheduled_maintenance_date > %s)
                ORDER BY 
                    v.performance_rating DESC, e.purchase_date ASC
                LIMIT %s
            """, (category, end, end, end, required_qty), as_dict=0)

            # Flatten result list
            available_ids = [x[0] for x in available_ids]

            if len(available_ids) < required_qty:
                frappe.throw(
                    f"Insufficient 'Ready' stock for <b>{category}</b>.<br><br>"
                    f"Required: {required_qty}<br>"
                    f"Found: {len(available_ids)}<br><br>"
                    f"Note: Equipment must have Insurance, Registration, and Maintenance valid until {self.expected_end_date}."
                )

            for eq_id in available_ids:
                self.append("equipment_list", {
                    "equipment_category": category,
                    "equipment_id": eq_id
                })
                frappe.db.set_value("Equipment", eq_id, "status", "Rented")
        
        self.db_update()
Key Improvements:
Legal Compliance: The query automatically skips equipment if its insurance or registration expires before the customer is supposed to return it.

Performance Priority: By joining with tabVendor, the system automatically grabs equipment from your "5-star" vendors first, ensuring the customer gets the most reliable fleet.

Maintenance Safety: It ensures the machine won't hit its "Scheduled Maintenance" date while out on the field.

Git Commit Message
Plaintext
feat(rentals): enhanced equipment allocation with rating and date validation

- Integrated Vendor performance_rating into auto-assignment logic.
- Added validation to ensure insurance and registration cover the rental duration.
- Added check to prevent renting equipment due for maintenance during the contract.
- Optimized allocation query using SQL JOIN for better performance prioritization.
Would you like me to add a "Warning" on the Rental Agreement Dashboard if any currently rented equipment is approaching its expiry dates while still on-site?

	def validate_dates(self):
		start_date = getdate(self.start_date)
		expected_end_date = getdate(self.expected_end_date)

		if expected_end_date < start_date:
			frappe.throw("Expected End Date cannot be before Start Date.")

	def calculate_totals(self):
		self.discount_percentage = flt(self.discount_percentage)

		if self.discount_percentage < 0 or self.discount_percentage > 100:
			frappe.throw("Discount Percentage must be between 0 and 100.")

		self.estimate_rental_days = date_diff(self.expected_end_date, self.start_date) + 1

		total_daily_rate = 0
		for item in self.items:
			total_daily_rate += item.total

		self.total_daily_rate = total_daily_rate
		self.estimated_total = self.total_daily_rate*self.estimate_rental_days
		self.discount_amount = self.estimated_total * self.discount_percentage / 100

		net_rental_total = self.estimated_total - self.discount_amount
		security_deposit_percentage = frappe.db.get_single_value("Rental Settings", "security_deposit_percentage") or 0
		self.security_deposit = net_rental_total * security_deposit_percentage / 100
		self.grand_total = net_rental_total + flt(self.security_deposit)
		


