frappe.ui.form.on('Employee', {
    refresh: function(frm) {

        frm.add_custom_button(__('Fetch EID Data'), async function() {
        try {
            // Show top progress bar
            frappe.show_progress(__('Fetching EID data...'), 0, 100);

            // Fake incremental progress (optional)
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 5, 90); // increase until 90%
                frappe.show_progress(__('Fetching EID data...'), progress, 100);
            }, 100);

            // Fetch EID data
            await fetchAndSetEID(frm);

            // Complete progress bar
            frappe.show_progress(__('Fetching EID data...'), 100, 100);
            clearInterval(progressInterval);

        } catch (error) {
            console.error(error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to fetch EID data.'),
                indicator: 'red'
            });
        } finally {
            // Remove progress bar after short delay
            setTimeout(() => {
                frappe.hide_progress();
            }, 300);
        }
    });


        frm.add_custom_button(__('Scan & Attach ID'), function() {

            let d = new frappe.ui.Dialog({
                title: __('Scan & Attach Identification'),
                fields: [
                    {
                        fieldname: 'mrz_input',
                        fieldtype: 'Small Text',
                        label: __('Document Scan Data'),
                        reqd: 0,
                        placeholder: __('Paste scanned document data here')
                    },
                    {
                        fieldname: 'fetch_scan_html',
                        fieldtype: 'HTML',
                        options: `
                            <button class="btn btn-secondary btn-sm" id="fetch-latest-scan-btn">
                                Load Latest Scan
                            </button>
                            <div id="scan-preview" style="margin-top:10px;"></div>
                        `
                    }
                ],
                primary_action_label: __('Apply & Save'),
                primary_action: async function() {

                    const values = d.get_values();
                    const mrz = values.mrz_input;

                    if (mrz) {
                        const parsed = parseMRZ(mrz);

                        if (parsed.forenames) frm.set_value('first_name', parsed.forenames);
                        if (parsed.surname) frm.set_value('last_name', parsed.surname);
                        if (parsed.date_of_birth) frm.set_value('date_of_birth', parseDate(parsed.date_of_birth));
                        if (parsed['doc._number'] || parsed.doc_number)
                            frm.set_value('passport_number', parsed['doc._number'] || parsed.doc_number);
                        if (parsed.nationality) frm.set_value('custom_nationality', parsed.nationality);
                        if (parsed.issuing_state) frm.set_value('place_of_issue', parsed.issuing_state);
                    }

                    let latest_doc = await frappe.db.get_list('Scanned Documents', {
                        fields: ['name', 'front_image', 'back_image'],
                        filters: [['owner', '=', frappe.session.user]],
                        order_by: 'creation desc',
                        limit: 1
                    });

                    if (latest_doc.length) {

                        const doc = latest_doc[0];
                        let attachments = [];

                        if (doc.front_image) {
                            let front_file = await frappe.db.get_value(
                                'File',
                                { file_url: doc.front_image },
                                'name'
                            );

                            if (front_file?.message?.name) {
                                attachments.push(front_file.message.name);
                            }
                        }

                        if (doc.back_image) {
                            let back_file = await frappe.db.get_value(
                                'File',
                                { file_url: doc.back_image },
                                'name'
                            );

                            if (back_file?.message?.name) {
                                attachments.push(back_file.message.name);
                            }
                        }

                        // if (attachments.length) {

                        //     await frappe.call({
                        //         method: "frappe.utils.file_manager.add_attachments",
                        //         args: {
                        //             doctype: frm.doctype,
                        //             name: frm.docname,
                        //             attachments: attachments
                        //         }
                        //     });

                        // }
                        if (latest_doc.length) {
                            const doc = latest_doc[0];

                            // Determine images to set
                            if (doc.is_single) {
                                // Single image → store in front image field
                                frm.set_value('custom_passport_front_image', doc.front_image || doc.back_image || '');
                                frm.set_value('custom_passport_back_image', ''); // empty back field
                            } else {
                                // Two images
                                frm.set_value('custom_passport_front_image', doc.front_image || '');
                                frm.set_value('custom_passport_back_image', doc.back_image || '');
                            }
                        }

                        // No need to call file_manager, field values are now set
                        frappe.msgprint({
                            title: __('Success'),
                            message: __('Scanned image(s) set successfully'),
                            indicator: 'green'
                        });
                    }

                    await frm.save();

                    // frappe.msgprint({
                    //     title: __('Success'),
                    //     message: __('Images attached successfully'),
                    //     indicator: 'green'
                    // });

                    d.hide();
                }
            });

            d.show();

            d.$wrapper.find('#fetch-latest-scan-btn').on('click', async function() {
                const preview = d.$wrapper.find('#scan-preview');

                let latest_doc = await frappe.db.get_list('Scanned Documents', {
                    fields: ['name', 'front_image', 'back_image','is_single'],
                    filters: [['owner', '=', frappe.session.user]],
                    order_by: 'creation desc',
                    limit: 1
                });

                if (!latest_doc.length) {
                    preview.html(`<p style="color:orange;">No scanned document found.</p>`);
                    return;
                }

                const doc = latest_doc[0];

                // Pick whichever image exists for single-side docs
                const single_image = doc.front_image || doc.back_image || '';

                let images_html = '';

                // SINGLE-SIDE DOCUMENT
                if (doc.is_single) {
                    images_html = `
                        <div style="text-align:center; margin-top:10px;">
                            <p><b>Scanned Image</b></p>
                            ${single_image ? `
                                <img src="${single_image}" style="width:100%; max-width:220px;">
                            ` : `
                                <p style="color:orange;">No image available</p>
                            `}
                        </div>
                    `;
                }
                // TWO-SIDE DOCUMENT
                else {
                    images_html = `
                        <div style="display:flex; gap:10px; margin-top:10px;">
                            <div style="text-align:center;">
                                <p><b>Scanned Image (Front)</b></p>
                                ${doc.front_image
                                    ? `<img src="${doc.front_image}" style="width:100%; max-width:200px;">`
                                    : `<p style="color:orange;">Missing</p>`
                                }
                            </div>
                            <div style="text-align:center;">
                                <p><b>Scanned Image (Back)</b></p>
                                ${doc.back_image
                                    ? `<img src="${doc.back_image}" style="width:100%; max-width:200px;">`
                                    : `<p style="color:orange;">Missing</p>`
                                }
                            </div>
                        </div>
                    `;
                }

                preview.html(`
                    <p><b>Scan Reference:</b> ${doc.name}</p>
                    ${images_html}
                `);


            });

        });

    }
});



// Helper: parse MRZ with multiple blocks and non-empty fields only
function parseMRZ(mrz_input) {
    const parsed = {};

    // Split input into blocks between START and END
    const blocks = mrz_input.split(/START|END/).map(b => b.trim()).filter(b => b);

    blocks.forEach(block => {
        // Skip block if all fields are empty
        const hasData = block.split('\n').some(line => {
            if (line.includes(':')) {
                const value = line.split(':').slice(1).join(':').trim();
                return value !== '';
            }
            return false;
        });
        if (!hasData) return;

        // Parse non-empty lines
        block.split('\n').forEach(line => {
            line = line.trim();
            if (line.includes(':')) {
                let [key, ...rest] = line.split(':');
                key = key.trim().toLowerCase().replace(/ /g, '_');
                const value = rest.join(':').trim();
                if (value) parsed[key] = value;
            }
        });
    });

    return parsed;
};
function parseDate(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return '';

    let day = parts[0].padStart(2, '0');
    let month = parts[1].padStart(2, '0');
    let year = parts[2];

    if (year.length === 2) {
        const yy = parseInt(year, 10);
        const currentYear = new Date().getFullYear() % 100; // last 2 digits of current year

        if (yy <= currentYear) {
            year = '20' + year;  // e.g., 23 → 2023
        } else {
            year = '19' + year;  // e.g., 94 → 1994
        }
    }

    return `${year}-${month}-${day}`;
}


// Helper function to safely set values
function setField(frm, fieldname, value) {
    frm.set_value(fieldname, value || '');
}





//Parse MRZ blocks safely (unchanged, solid)

function parseMRZ(mrz_input) {
    const parsed = {};

    const blocks = mrz_input
        .split(/START|END/)
        .map(b => b.trim())
        .filter(b => b);

    blocks.forEach(block => {
        const hasData = block.split('\n').some(line => {
            if (line.includes(':')) {
                const value = line.split(':').slice(1).join(':').trim();
                return value !== '';
            }
            return false;
        });
        if (!hasData) return;

        block.split('\n').forEach(line => {
            line = line.trim();
            if (line.includes(':')) {
                let [key, ...rest] = line.split(':');
                key = key.trim().toLowerCase().replace(/ /g, '_');
                const value = rest.join(':').trim();
                if (value) parsed[key] = value;
            }
        });
    });

    return parsed;
}

/**
 * Normalize date to YYYY-MM-DD
 * Supports:
 *  - DD/MM/YYYY  (EID)
 *  - DD-MM-YYYY
 *  - DD-MM-YY    (MRZ)
 */
function normalizeDateToYMD(dateStr) {
    if (!dateStr) return '';

    const separator = dateStr.includes('/') ? '/' : '-';
    const parts = dateStr.split(separator);

    if (parts.length !== 3) return '';

    let [day, month, year] = parts.map(p => p.trim());

    // Handle 2-digit year (MRZ)
    if (year.length === 2) {
        const yy = parseInt(year, 10);
        const currentYY = new Date().getFullYear() % 100;
        year = yy <= currentYY ? `20${year}` : `19${year}`;
    }

    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}
function mapGender(gender) {
    if (!gender) return '';
    const g = gender.toUpperCase();
    if (g === 'M') return 'Male';
    if (g === 'F') return 'Female';
    return '';
}

async function fetchAndSetEID(frm) {
    try {
        const response = await fetch(
            'http://localhost:9005/api/EidServices/Read_Data_EID',
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            frappe.msgprint({
                title: __('EID Reader Error'),
                message: __('Failed to connect to the EID reader.'),
                indicator: 'red'
            });
            return;
        }

        let data = await response.json();
        if (typeof data === 'string') data = JSON.parse(data);

        console.log('Parsed EID response:', data);

        if (!data.EID) {
            frappe.msgprint({
                title: __('EID Reader'),
                message: __('No card detected or data not available.'),
                indicator: 'orange'
            });
            return;
        }

        //MAIN FORM FIELDS
        
        frm.set_value('first_name', data.Name || '');
        frm.set_value('custom_employee_name_in_arabic', data.NameAr || '');
        // frm.set_value('gender', data.Gender || '');
        frm.set_value('gender', mapGender(data.Gender));
        frm.set_value('custom_nationality', data.Nationality || '');

        frm.set_value(
            'date_of_birth',
            normalizeDateToYMD(data.DOB)
        );

        // CHILD TABLE Fields
        
        frm.clear_table('custom_emirates_id_info');

        const row = frm.add_child('custom_emirates_id_info');

        row.emirates_id_no = data.EID || '';
        row.issuance_date = normalizeDateToYMD(data.IssueDate);
        row.expiry_date = normalizeDateToYMD(data.Expiry);
        // NEW FIELDS
        frm.set_value('personal_email', data.Email || '');
        frm.set_value('cell_number', data.Phone || '');
        
        // Image field (must be Image type)
        row.emirates_id_attachment = data.Photo
            ? `data:image/jpeg;base64,${data.Photo}`
            : '';
        // Set the signature image in the main form field
        frm.set_value(
            'custom_eid_signature',
            data.PhotoSignature
                ? `data:image/tiff;base64,${data.PhotoSignature}`
                : ''
        );
        
        frm.refresh_field('custom_emirates_id_info');
        await frm.save();

        frappe.msgprint({
            title: __('Success'),
            message: __('EID data fetched successfully!'),
            indicator: 'green'
        });

    } catch (error) {
        console.error('Failed to fetch EID data:', error);
        frappe.msgprint({
            title: __('EID Reader Error'),
            message: error.message,
            indicator: 'red'
        });
    }
}

