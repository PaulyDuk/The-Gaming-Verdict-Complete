// Shared utility functions for checkboxes and toggling full content

/**
 * Select all checkboxes matching a selector
 */
function selectAllCheckboxes(selector) {
    document.querySelectorAll(selector).forEach(checkbox => {
        if (!checkbox.disabled) checkbox.checked = true;
    });
}

/**
 * Deselect all checkboxes matching a selector
 */
function deselectAllCheckboxes(selector) {
    document.querySelectorAll(selector).forEach(checkbox => {
        if (!checkbox.disabled) checkbox.checked = false;
    });
}

/**
 * Toggle full content display for a preview element
 * @param {HTMLElement} link - The link/button clicked
 * @param {string} previewClass - The preview container class
 * @param {string} fullClass - The full content class
 */
function toggleFullContent(link, previewClass, fullClass) {
    const previewDiv = link.closest('.' + previewClass);
    const fullContent = previewDiv.querySelector('.' + fullClass);
    if (fullContent.style.display === 'none' || !fullContent.style.display) {
        fullContent.style.display = 'block';
        link.style.display = 'none';
    } else {
        fullContent.style.display = 'none';
        previewDiv.querySelector('a').style.display = 'inline';
    }
}

/**
 * Universal select all function for populate pages
 */
function selectAll() {
    // Try all possible checkbox selectors
    const selectors = ['.game-checkbox:not(:disabled)', '.developer-checkbox:not(:disabled)', '.publisher-checkbox:not(:disabled)'];
    
    for (const selector of selectors) {
        const checkboxes = document.querySelectorAll(selector);
        if (checkboxes.length > 0) {
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
                const index = checkbox.value;
                // Trigger the appropriate toggle function
                if (selector.includes('game')) {
                    if (typeof toggleGameData === 'function') toggleGameData(checkbox, index);
                } else if (selector.includes('developer')) {
                    if (typeof toggleDeveloperData === 'function') toggleDeveloperData(checkbox, index);
                } else if (selector.includes('publisher')) {
                    if (typeof togglePublisherData === 'function') togglePublisherData(checkbox, index);
                }
            });
            break;
        }
    }
}

/**
 * Universal deselect all function for populate pages
 */
function deselectAll() {
    // Try all possible checkbox selectors
    const selectors = ['.game-checkbox', '.developer-checkbox', '.publisher-checkbox'];
    
    for (const selector of selectors) {
        const checkboxes = document.querySelectorAll(selector);
        if (checkboxes.length > 0) {
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
                const index = checkbox.value;
                // Trigger the appropriate toggle function
                if (selector.includes('game')) {
                    if (typeof toggleGameData === 'function') toggleGameData(checkbox, index);
                } else if (selector.includes('developer')) {
                    if (typeof toggleDeveloperData === 'function') toggleDeveloperData(checkbox, index);
                } else if (selector.includes('publisher')) {
                    if (typeof togglePublisherData === 'function') togglePublisherData(checkbox, index);
                }
            });
            break;
        }
    }
}

/**
 * Universal select all existing items function for populate pages
 */
function selectAllExisting() {
    // Try all possible existing checkbox selectors
    const selectors = ['.existing-review-checkbox', '.existing-developer-checkbox', '.existing-publisher-checkbox'];
    
    for (const selector of selectors) {
        const checkboxes = document.querySelectorAll(selector);
        if (checkboxes.length > 0) {
            selectAllCheckboxes(selector);
            break;
        }
    }
}

/**
 * Universal deselect all existing items function for populate pages
 */
function deselectAllExisting() {
    // Try all possible existing checkbox selectors
    const selectors = ['.existing-review-checkbox', '.existing-developer-checkbox', '.existing-publisher-checkbox'];
    
    for (const selector of selectors) {
        const checkboxes = document.querySelectorAll(selector);
        if (checkboxes.length > 0) {
            deselectAllCheckboxes(selector);
            break;
        }
    }
}

/**
 * Attach score listeners for reviews populate page
 */
function attachScoreListeners() {
    const scoreInputs = document.querySelectorAll('.review-score');
    scoreInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (typeof updateCreateButton === 'function') {
                updateCreateButton();
            }
        });
    });
}
