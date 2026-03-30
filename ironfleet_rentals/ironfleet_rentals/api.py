import frappe

@frappe.whitelist()
def get_leaf_nodes_parent(doctype, txt, searchfield, start, page_len, filters):
    parent_nodes=set(frappe.db.get_list("Equipment Category",{"is_group":0},pluck="parent_equipment_category"))
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