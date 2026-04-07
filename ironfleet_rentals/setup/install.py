import frappe

def after_install():
    if not frappe.db.exists("Rental Settings"):
        doc = frappe.get_doc({
            "doctype": "Rental Settings",
            "late_fee_per_day": 500,
            "default_currency": "USD"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()