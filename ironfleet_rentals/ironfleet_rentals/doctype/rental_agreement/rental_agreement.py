# Copyright (c) 2026, IronFleet_Rentals and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, add_days

class RentalAgreement(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_totals()

	def before_submit(self):
		self.validate_and_assign_equipment()
		self.create_payment_schedule()

	def on_cancel(self):
		for row in self.equipment_list:
			if row.equipment_id:
				frappe.db.set_value("Equipment", row.equipment_id, "status", "Available")

	def validate_and_assign_equipment(self):
		self.set("equipment_list", [])
		end = getdate(self.expected_end_date)
		for item in self.items:
			category = item.equipment_categorys
			required_qty = int(item.qty)
			# 1. Search for OWNED physical equipment first
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
			found_physical = len(available_ids)
			# 2. If physical stock is insufficient, check for a SUBMITTED Sourcing Document
			if found_physical < required_qty:
				needed_from_sourcing = required_qty - found_physical
				# Check if a Sourcing Request exists for this RA and Category
				sourced_qty = frappe.db.sql("""
					SELECT SUM(si.qty) 
					FROM `tabSourcing Items` si
					JOIN `tabSubcontract Sourcing` ss ON si.parent = ss.name
					WHERE ss.rental_agreement = %s 
					AND si.equipment_category = %s
					AND ss.docstatus = 1
				""", (self.name, category))[0][0] or 0
				# If (Physical + Sourced) is still less than Required, Block Submission
				
				if (found_physical + sourced_qty) < required_qty:
					frappe.throw(
						f"Insufficient 'Ready' stock and no Sourcing found for <b>{category}</b>.<br><br>"
						f"Required: {required_qty}<br>"
						f"Physical Available: {found_physical}<br>"
						f"Sourced via Subcontract: {sourced_qty}<br><br>"
						f"Note: Please submit a Sourcing Request for the remaining {required_qty - found_physical} units."
					)
			for eq_id in available_ids:
				self.append("equipment_list", {
					"equipment_category": category,
					"equipment_id": eq_id
				})
				frappe.db.set_value("Equipment", eq_id, "status", "Rented")

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
			total_daily_rate += flt(item.total)

		self.total_daily_rate = total_daily_rate
		self.estimated_total = self.total_daily_rate * self.estimate_rental_days
		self.discount_amount = self.estimated_total * (self.discount_percentage / 100)

		net_rental_total = self.estimated_total - self.discount_amount

		security_deposit_percentage = frappe.db.get_single_value("Rental Settings", "security_deposit_percentage") or 0
		self.security_deposit = net_rental_total * flt(security_deposit_percentage) / 100
		self.grand_total = net_rental_total + flt(self.security_deposit)
		if self.payment_schedule:
			self.update_payment_status()
		
	def create_payment_schedule(self):
		if self.payment_schedule:
			return
		
		# Configuration: 30% Advance, 40% Mid, 30% Final
		terms = [
			{"term": "Advance", "ratio": 0.30, "days": 0},
			{"term": "Mid-Rental", "ratio": 0.40, "days": int(self.estimate_rental_days / 2)},
			{"term": "Final Settlement", "ratio": 0.30, "days": self.estimate_rental_days}
		]

		for t in terms:
			due_date = add_days(self.start_date, t['days'])
			amount = flt(self.grand_total) * t['ratio']
			
			self.append("payment_schedule", {
				"payment_term": t['term'],
				"due_date": due_date,
				"amount": amount,
				"status": "Unpaid"
			})

		self.update_payment_status()
	def update_payment_status(self):
		total_paid=0
		for row in self.get("payment_schedule"):
			if row.status == "Paid":
				total_paid+=row.amount
		self.out_standing_amount = self.grand_total - total_paid
		if self.out_standing_amount <= 0 and self.grand_total > 0:
			self.is_fully_paid = 1
		else:
			self.is_fully_paid = 0
