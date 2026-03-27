import frappe

@frappe.whitelist()
def get_leaf_nodes_parent(doctype, txt, searchfield, start, page_len, filters):
    parent_nodes=set(frappe.db.get_list("Equipment Category",{"is_group":0},pluck="parent_equipment_category"))
    l=[(p,p) for p in parent_nodes if p]
    if txt:
        parent_nodes = [p for p in parent_nodes if txt.lower() in p.lower()]
    return [(p,p) for p in parent_nodes if p]