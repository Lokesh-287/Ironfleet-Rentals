import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, add_years, today

class Equipment(Document):

	def before_insert(self):
		self.set_default_values()

	def validate(self):
		self.validate_dates()
		self.validate_rental_rate()


	def set_default_values(self):

		purchase_date = getdate(self.purchase_date or today())

		# Default Status
		if not self.status:
			self.status = "Available"

		# Current Location
		if not self.current_location:
			self.current_location = "Main Warehouse"

		# Maintenance → +30 days
		if not self.next_scheduled_maintenance_date:
			self.next_scheduled_maintenance_date = add_days(purchase_date, 30)

		# Insurance → +1 year
		if not self.insurance_expired_date:
			self.insurance_expired_date = add_years(purchase_date, 1)

		# Registration → +1 year
		if not self.registration_expired_date:
			self.registration_expired_date = add_years(purchase_date, 1)

	def validate_dates(self):
		today_date = getdate(today())

		if self.purchase_date and getdate(self.purchase_date) > today_date:
			frappe.throw("Purchase Date cannot be in future")

		if self.insurance_expired_date and self.purchase_date:
			if getdate(self.insurance_expired_date) < getdate(self.purchase_date):
				frappe.throw("Insurance Expiry must be after Purchase Date")

		if self.registration_expired_date and self.purchase_date:
			if getdate(self.registration_expired_date) < getdate(self.purchase_date):
				frappe.throw("Registration Expiry must be after Purchase Date")

	def validate_rental_rate(self):
		rate = float(self.default_daily_rental_rate or 0)
		if rate <= 0:
			frappe.throw("Rental rate must be greater than 0")