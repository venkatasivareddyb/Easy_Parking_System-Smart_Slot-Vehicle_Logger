// OCR Image Preview
function previewImage(event) {
    const fileInput = event.target;
    const preview = document.getElementById('image-preview');
    if (fileInput && preview) {
        preview.src = URL.createObjectURL(fileInput.files[0]);
        preview.style.display = 'block';
    }
}

// Company search filter (admin)
function filterCompanies() {
    const input = document.getElementById("companySearch");
    const filter = input.value.toUpperCase();
    const table = document.getElementById("companyTable");
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        const td = tr[i].getElementsByTagName("td")[0]; // First column
        if (td) {
            const txtValue = td.textContent || td.innerText;
            tr[i].style.display = txtValue.toUpperCase().includes(filter) ? "" : "none";
        }
    }
}

// Toggle admin company form
function toggleForm() {
    const form = document.getElementById('companyForm');
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
}

// Toggle vehicle entry form (user)
function toggleEntryForm() {
    const form = document.getElementById('entryForm');
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
}

// Toggle profile section
function toggleProfileSection() {
    const section = document.getElementById("profileSection");
    section.style.display = section.style.display === "none" || section.style.display === "" ? "block" : "none";
}

// Toggle edit form in profile section
function toggleEditForm() {
    const form = document.getElementById("editForm");
    form.style.display = form.style.display === "none" || form.style.display === "" ? "block" : "none";
}

// Email auto-generation on registration and edit modal
function updateEmailPreview() {
    const usernameField = document.querySelector('[name="username"]');
    const companyField = document.querySelector('[name="company_name"]');
    const emailField = document.getElementById('generatedEmail');

    if (!usernameField || !companyField || !emailField) return;

    const username = usernameField.value;
    const company = companyField.value;

    if (username && company) {
        const cleanedCompany = company.toLowerCase().replace(/\s+/g, '');
        emailField.value = `${username}@${cleanedCompany}.com`;
    } else {
        emailField.value = '';
    }
}

// ✅ Run safely after all HTML loads
document.addEventListener("DOMContentLoaded", function () {
    // OCR Image Preview
    const fileInput = document.getElementById('imageInput');
    const preview = document.getElementById('image-preview');
    if (fileInput && preview) {
        fileInput.addEventListener('change', function (event) {
            preview.src = URL.createObjectURL(event.target.files[0]);
            preview.style.display = 'block';
        });
    }

    // Company search filter (admin)
    const companySearch = document.getElementById("companySearch");
    const companyTable = document.getElementById("companyTable");
    if (companySearch && companyTable) {
        companySearch.addEventListener("input", function () {
            const filter = companySearch.value.toUpperCase();
            const tr = companyTable.getElementsByTagName("tr");
            for (let i = 1; i < tr.length; i++) {
                let td = tr[i].getElementsByTagName("td")[0];
                if (td) {
                    let txtValue = td.textContent || td.innerText;
                    tr[i].style.display = txtValue.toUpperCase().includes(filter) ? "" : "none";
                }
            }
        });
    }

    // Toggle company form
    const toggleCompanyFormBtn = document.getElementById('toggleCompanyForm');
    const companyForm = document.getElementById('companyForm');
    if (toggleCompanyFormBtn && companyForm) {
        toggleCompanyFormBtn.addEventListener('click', function () {
            companyForm.style.display = companyForm.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Toggle vehicle entry form
    const toggleEntryFormBtn = document.getElementById('toggleEntryForm');
    const entryForm = document.getElementById('entryForm');
    if (toggleEntryFormBtn && entryForm) {
        toggleEntryFormBtn.addEventListener('click', function () {
            entryForm.style.display = entryForm.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Update email preview during company registration
    const usernameInput = document.querySelector('[name="username"]');
    const companyInput = document.querySelector('[name="company_name"]');
    const emailField = document.getElementById('generatedEmail');

    if (usernameInput && companyInput && emailField) {
        usernameInput.addEventListener('input', updateEmailPreview);
        companyInput.addEventListener('input', updateEmailPreview);
    }

    // Email generation inside edit modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function () {
            const usernameInput = modal.querySelector('input[name="username"]');
            const companyInput = modal.querySelector('input[name="company_name"]');
            const emailInput = modal.querySelector('.generated-email');

            if (usernameInput && companyInput && emailInput) {
                const username = usernameInput.value.trim().toLowerCase().replace(/\s+/g, '');
                const company = companyInput.value.trim().toLowerCase().replace(/\s+/g, '');
                emailInput.value = `${username}@${company}.com`;
            }
        });
    });
});
