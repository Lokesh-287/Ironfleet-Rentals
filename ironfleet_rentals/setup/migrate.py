import frappe

def after_migrate():
    # Ensure all equipment has a status; if null, set to Available
    frappe.db.sql("""
        UPDATE `tabEquipment` 
        SET status = 'Available' 
        WHERE status IS NULL OR status = ''
    """)