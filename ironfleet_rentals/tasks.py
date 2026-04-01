import frappe
from frappe.utils import add_days, today, get_url_to_form

def check_maintenance_schedules():
	settings = frappe.get_single("Rental Settings")
	window = settings.maintenance_reminder_days or 7
	threshold_date = add_days(today(), int(window))

	due_equipment = frappe.get_all("Equipment", 
		filters={
			"next_scheduled_maintenance_date": ["<=", threshold_date],
			"status": ["not in", ["Retired", "Under Maintenance"]]
		},
		fields=["name", "equipment_catgory", "next_scheduled_maintenance_date"]
	)

	for eq in due_equipment:
		if not frappe.db.exists("Maintenance Schedule", {
			"equipment": eq.name, 
			"status": ["in", ["Scheduled", "Assigned", "In Progress"]]
		}):
			maint = frappe.get_doc({
				"doctype": "Maintenance Schedule",
				"equipment": eq.name,
				"maintenance_type": "Preventive",
				"status": "Scheduled",
				"scheduled_date": today(),
				"description": f"Auto-generated preventive maintenance for {eq.name}."
			})
			maint.insert(ignore_permissions=True)

			send_maintenance_alert(maint, eq)

def send_maintenance_alert(maint_doc, eq_data):
	"""Sends an email to the Maintenance Manager role"""
	
	recipients = frappe.get_all("Has Role", 
		filters={"role": "Maintenance Manager"}, 
		pluck="parent"
	)

	if recipients:
		doc_link = get_url_to_form("Maintenance Schedule", maint_doc.name)
		
		frappe.sendmail(
			recipients=recipients,
			subject=f"Maintenance Due: {maint_doc.equipment}",
			message=f"""
				<h3>Maintenance Alert</h3>
				<p>Equipment <b>{maint_doc.equipment}</b> ({eq_data.equipment_catgory}) is due for maintenance on {eq_data.next_scheduled_maintenance_date}.</p>
				<p>A new <b>Preventive Maintenance Schedule</b> has been created: <b>{maint_doc.name}</b>.</p>
				<p><a href="{doc_link}">Click here to view and assign a technician.</a></p>
			""",
			delayed=False
		)