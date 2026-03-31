import frappe
from frappe.utils import flt
@frappe.whitelist()
def get_leaf_nodes(doctype, txt, searchfield, start, page_len, filters):
    # parent_nodes=set(frappe.db.get_list("Equipment Category",{"is_group":0},pluck="parent_equipment_category"))
    # l=[(p,p) for p in parent_nodes if p]
    # if txt:
    #     parent_nodes = [p for p in parent_nodes if txt.lower() in p.lower()]
    # return [(p,p) for p in parent_nodes if p]

    parent_nodes=set(frappe.db.get_list("Equipment Category",{"is_group":0},pluck="name"))
    l=[(p,p) for p in parent_nodes if p]
    if txt:
        parent_nodes = [p for p in parent_nodes if txt.lower() in p.lower()]
    return [(p,p) for p in parent_nodes if p]
    
#------------------------------------------------------------------------------------------------------------------
@frappe.whitelist()
def get_daily_rate(equipment_category):
    eq=equipment_category
    while True:
        equipment_data=frappe.db.get_value("Equipment Category",equipment_category,["default_daily_rental_rate","parent_equipment_category"],
        as_dict=True
        )
        if equipment_data.get("default_daily_rental_rate"):
            return equipment_data["default_daily_rental_rate"]
        if not equipment_data.get("parent_equipment_category"):
                frappe.throw(f"{eq} has no default_daily_rental_rate please set default_daily_rental_rate before making Aggrement ")
        equipment_category = equipment_data["parent_equipment_category"]

#------------------------------------------------------------------------------------------------------------------
@frappe.whitelist()
def get_vendor_equipment_categorys(doctype, txt, searchfield, start, page_len, filters):
    vendor=filters.get("vendor")
    if not vendor:
        return []
    equipment_category = frappe.get_all("Equipment Categorys",filters={"parent": vendor},pluck="equipment_category")
    if txt:
        equipment_category=[eq for eq in equipment_category if txt.lower() in eq.lower()]
    return [(eq,eq) for eq in equipment_category if eq]

#------------------------------------------------------------------------------------------------------------------
@frappe.whitelist()
def create_equipment_records(equipment_category, qty, vendor, purchase_date,default_rate):
    for i in range(int(qty)):
        frappe.get_doc({
            "doctype": "Equipment",
            "equipment_catgory": equipment_category,
            "status": "Available",
            "vendor": vendor,
            "purchase_date": purchase_date,
            "default_daily_rental_rate":default_rate
        }).insert()
    return "Created"
#------------------------------------------------------------------------------------------------------------------
@frappe.whitelist()
def create_sourcing_request(rental_agreement, items):
    if isinstance(items, str):
        items = frappe.parse_json(items)
    
    # NEW: Fetch Rental Agreement dates for validation
    ra_dates = frappe.db.get_value("Rental Agreement", rental_agreement, 
                                  ["start_date", "expected_end_date"], as_dict=True)
    
    if not ra_dates:
        frappe.throw("Rental Agreement dates not found.")
        
    end_date = ra_dates.expected_end_date

    # 1. Get available internal stock (Filtering out units with expiring dates)
    # We only count stock that is 'Ready' for the WHOLE duration
    available_stocks = frappe.db.sql("""
         SELECT equipment_catgory, COUNT(name) AS available_qty
         FROM `tabEquipment`
         WHERE status = 'Available' 
         AND `condition` != 'Damaged'
         AND (insurance_expired_date IS NULL OR insurance_expired_date > %s)
         AND (registration_expired_date IS NULL OR registration_expired_date > %s)
         AND (next_scheduled_maintenance_date IS NULL OR next_scheduled_maintenance_date > %s)
         GROUP BY equipment_catgory
    """, (end_date, end_date, end_date), as_dict=1)

    available_map = {d.equipment_catgory: d.available_qty for d in available_stocks}

    # 2. Calculate shortages
    sourcing_items = {}
    for item in items:
        cat = item.get("equipment_categorys")
        req_qty = flt(item.get("qty"))
        avail_qty = available_map.get(cat, 0)

        if req_qty > avail_qty:
            shortage = req_qty - avail_qty
            sourcing_items[cat] = sourcing_items.get(cat, 0) + shortage

    if not sourcing_items:
        return {"status": "none", "message": "All items are available in stock and meet date requirements."}

    # 3. Search for Vendors
    final_items_to_source = []
    missing_vendor_categories = []

    # for cat, qty in sourcing_items.items():
    #     best_vendor = frappe.db.sql("""
    #         SELECT v.name 
    #         FROM `tabVendor` v
    #         JOIN `tabEquipment Categorys` ec ON v.name = ec.parent
    #         WHERE ec.equipment_category = %s 
    #         AND v.vendor_type = 'Subcontractor'
    #         AND v.status = 'Active' 
    #         ORDER BY v.performance_rating DESC
    #         LIMIT 1
    #     """, (cat), as_dict=1)
    for cat, qty in sourcing_items.items():
        best_vendor = frappe.db.sql("""
            SELECT v.name 
            FROM `tabVendor` v
            JOIN `tabEquipment Categorys` ec ON v.name = ec.parent
            WHERE ec.equipment_category = %s 
            AND v.vendor_type = 'Subcontractor'
            ORDER BY v.performance_rating DESC
            LIMIT 1
        """, (cat), as_dict=1)

        if best_vendor:
            final_items_to_source.append({
                "category": cat,
                "qty": qty,
                "vendor": best_vendor[0].name
            })
        else:
            missing_vendor_categories.append(cat)

    if missing_vendor_categories:
        return {
            "status": "missing_vendor",
            "categories": missing_vendor_categories,
            "message": "No subcontractors found for some categories."
        }

    # 5. Create the Sourcing Doc
    sourcing_doc = frappe.get_doc({
        "doctype": "Subcontract Sourcing",
        "rental_agreement": rental_agreement,
        "sourcing_date": frappe.utils.today(),
        "status": "Draft",
        "sourcing_items": []
    })

    for entry in final_items_to_source:
        sourcing_doc.append("sourcing_items", {
            "equipment_category": entry["category"],
            "qty": entry["qty"],
            "vendor": entry["vendor"]
        })

    sourcing_doc.insert()
    return {"status": "success", "docname": sourcing_doc.name}

#------------------------------------------------------------------------------------------------------------------

@frappe.whitelist()
def quick_create_vendor(categories):
    # categories will come as a JSON list from JS
    if isinstance(categories, str):
        categories = frappe.parse_json(categories)

    vendor_doc = frappe.get_doc({
        "doctype": "Vendor",
        "vendor_type": "Subcontractor",
        "equipment_categories": []
    })

    for cat in categories:
        vendor_doc.append("equipment_categories", {
            "equipment_category": cat,
            "availability_type":"Subcontract"
        })

    # This handles the Naming Series correctly on the server side
    vendor_doc.insert()
    
    return vendor_doc.name

#------------------------------------------------------------------------------------------------------------------
@frappe.whitelist()
def capture_rental_payment(rental_agreement,row_id,reference_no,payment_mode):
    frappe.db.set_value("Rental Payment Schedule",row_id,{
        "status":"Paid",
        "payment_reference": f"{payment_mode}: {reference_no}"
	})
    doc = frappe.get_doc("Rental Agreement", rental_agreement)
    doc.update_payment_status()
    doc.db_update()
    return doc.out_standing_amount