// Toggle developer data visibility based on checkbox selection
function toggleDeveloperData(checkbox, index) {
    const row = checkbox.closest('tr');
    const hiddenInput = row.querySelector('.developer-data');
    
    // Check if this developer already exists (should be disabled anyway)
    const exists = row.classList.contains('table-warning');
    if (exists) {
        checkbox.checked = false;
        checkbox.disabled = true;
        return;
    }

    if (checkbox.checked) {
        if (hiddenInput) hiddenInput.disabled = false;
        row.classList.add('table-success');
    } else {
        if (hiddenInput) hiddenInput.disabled = true;
        row.classList.remove('table-success');
    }
    
    if (typeof updateCreateButton === 'function') {
        updateCreateButton();
    }
}


