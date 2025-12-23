// frappe.ui.form.on("Scanned Documents", {
//     refresh: function(frm) {
//         // Show button only if both images exist
//         if(frm.doc.front_image && frm.doc.back_image) {
//             frm.add_custom_button(__('Attach to Employee'), function() {
                
//                 frappe.prompt([
//                     {
//                         fieldname: 'employee',
//                         fieldtype: 'Link',
//                         options: 'Employee',
//                         label: 'Select Employee',
//                         reqd: 1
//                     }
//                 ],
//                 function(values){
//                     const employee_name = values.employee;

//                     // Update the Employee document via frappe.db.set_value
//                     frappe.db.set_value('Employee', employee_name, {
//                         custom_passport_front_image: frm.doc.front_image,
//                         custom_passport_back_image: frm.doc.back_image
//                     }).then(() => {
//                         frappe.msgprint(__('Images attached to Employee successfully!'));
//                     });

//                 },
//                 __('Attach to Employee'),
//                 __('Update'));
//             });
//         }
//     }
// });
