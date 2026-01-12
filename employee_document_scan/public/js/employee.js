frappe.ui.form.on('Employee', {
    refresh: function(frm) {

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

                    frm.save();
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
}


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



