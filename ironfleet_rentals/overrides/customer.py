import frappe
from ironfleet_rentals.ironfleet_rentals.doctype.customer.customer import Customer

class IronFleetCustomer(Customer):
    def validate(self):
        super().validate()
        
        if not self.email_id:
            frappe.throw("IronFleet Policy: Email ID is mandatory for Safety Recall notifications.")
            
    def on_trash(self):
        if frappe.db.exists("Equipment", {"customer": self.name, "status": "Rented"}):
            frappe.throw("Cannot delete Customer while they have active equipment rentals.")