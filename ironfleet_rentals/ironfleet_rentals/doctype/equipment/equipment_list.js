frappe.listview_settings['Equipment'] = {
    refresh: function (listview) {
        // Use listview.page.add_inner_button to add a button to the top bar
        listview.page.add_inner_button(__('Process Bulk Recall'), () => {
            frappe.prompt([
                {
                    label: 'Select Category to Recall',
                    fieldname: 'category',
                    fieldtype: 'Link',
                    options: 'Equipment Category',
                    reqd: 1
                }
            ], (values) => {
                frappe.call({
                    method: "ironfleet_rentals.ironfleet_rentals.api.trigger_bulk_recall",
                    args: { category: values.category },
                    callback: function (r) {
                        if (r.message) {
                            let m = r.message;
                            frappe.msgprint({
                                title: __('Recall Summary'),
                                indicator: 'green',
                                message: `<b>Total:</b> ${m.total}<br><b>Processed:</b> ${m.processed}<br><b>Notices Sent:</b> ${m.rented}`
                            });
                            listview.refresh();
                        }
                    }
                });
            }, __('Initiate Manufacturer Recall'), __('Start Process'));
        }, __('Actions')); // This puts it under the "Actions" dropdown menu
    }
};