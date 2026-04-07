frappe.ui.form.on('Customer', {
    refresh: function (frm) {
        frm.add_custom_button('View Active Rentals', function () {
            frappe.set_route('List', 'Rental Agreement', {
                'customer': frm.doc.name,
                'status': ['in', ['Approved', 'Pending Ops', 'Pending Finance']]
            });
        }, 'IronFleet Actions');
    }
});