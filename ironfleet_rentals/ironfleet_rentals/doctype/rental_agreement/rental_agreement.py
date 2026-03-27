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
