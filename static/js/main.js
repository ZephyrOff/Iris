document.addEventListener('DOMContentLoaded', () => {
    const contentArea = document.getElementById('content-area');
    const genericModal = document.getElementById('generic-modal');
    const genericModalContent = document.getElementById('generic-modal-content');
    let currentPath = '/admin/dashboard-content'; // Variable to track the current loaded content

    // Function to display flash messages
    function showFlashMessage(message, category) {
        const flashContainer = document.createElement('div');
        flashContainer.className = `p-4 mb-6 rounded-lg text-sm font-medium ${category === 'danger' ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-green-100 text-green-700 border border-green-200'}`;
        flashContainer.textContent = message;
        contentArea.prepend(flashContainer);
        setTimeout(() => flashContainer.remove(), 5000); // Remove after 5 seconds
    }

    async function loadContent(path) {
        let activeElementId = null;
        let activeElementSelectionStart = null;

        // Store active element's ID and cursor position before content is replaced
        if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA')) {
            activeElementId = document.activeElement.id;
            activeElementSelectionStart = document.activeElement.selectionStart;
        }

        try {
            const response = await fetch(path, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest' // Indicate AJAX request
                }
            });

            // Check for redirects
            if (response.redirected) {
                window.location.href = response.url; // Follow the redirect
                return; // Stop further processing
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const html = await response.text();
            contentArea.innerHTML = html;
            currentPath = path; // Update the current path

            // Re-attach event listeners for newly loaded content
            attachEventListeners(contentArea);
            updateActiveNavLink(); // Call to update active link

            // Restore focus and cursor position
            if (activeElementId) {
                const restoredElement = document.getElementById(activeElementId);
                if (restoredElement && (restoredElement.tagName === 'INPUT' || restoredElement.tagName === 'TEXTAREA')) {
                    restoredElement.focus();
                    if (activeElementSelectionStart !== null) {
                        restoredElement.setSelectionRange(activeElementSelectionStart, activeElementSelectionStart);
                    }
                }
            }

        } catch (error) {
            console.error('Error loading content:', error);
            showFlashMessage('Failed to load content.', 'danger');
        }
    }

    // Function to update the active navigation link
    function updateActiveNavLink() {
        document.querySelectorAll('header nav a').forEach(link => {
            link.classList.remove('active-nav-link');
            const linkPath = link.dataset.path || link.getAttribute('href'); // Get data-path or href

            // Special handling for home link and dashboard
            if (linkPath === '/' && (currentPath === '/admin/dashboard-content' || currentPath === '/')) {
                link.classList.add('active-nav-link');
            } else if (linkPath && currentPath.startsWith(linkPath)) {
                // For other links, check if currentPath starts with the link's path
                link.classList.add('active-nav-link');
            }
        });
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest' // Indicate AJAX request
                }
            });

            // Check for redirects
            if (response.redirected) {
                window.location.href = response.url; // Follow the redirect
                return; // Stop further processing
            }

            const result = await response.json();

            if (result.success) {
                //showFlashMessage(result.message || 'Operation successful!', 'success');
                if (result.html && form.dataset.updateTarget) {
                    const targetElement = document.getElementById(form.dataset.updateTarget);
                    if (targetElement) {
                        targetElement.outerHTML = result.html;
                        attachEventListeners(document.getElementById(form.dataset.updateTarget));
                        updateActiveNavLink(); // Call to update active link
                    }
                } else if (result.redirect_url) {
                    // If a redirect URL is provided, load that content
                    loadContent(result.redirect_url);
                } else {
                    // Otherwise, reload current content to reflect changes
                    loadContent(currentPath);
                }
                // If form was in a modal, close it
                if (form.closest('#generic-modal')) {
                    closeModal();
                }
            } else {
                showFlashMessage(result.message || 'Operation failed.', 'danger');
                // If form submission failed, and it was a modal form, reload the form content
                if (form.closest('#generic-modal')) {
                    const currentModalUrl = form.action.replace('/create', '-form').replace('/edit', '-content'); // Adjust URL for GET request
                    window.openGenericModal(currentModalUrl); // Reload form
                }
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            showFlashMessage('An error occurred during submission.', 'danger');
        }
    }

    // Function to attach event listeners to newly loaded content
    function attachEventListeners(element) {
        // Attach click listeners for navigation links (internal to content area)
        element.querySelectorAll('a[data-path]').forEach(link => {
            link.removeEventListener('click', handleNavLinkClick); // Prevent duplicate listeners
            link.addEventListener('click', handleNavLinkClick);
        });

        // Attach submit listeners for forms with data-form-ajax attribute
        element.querySelectorAll('form[data-form-ajax]').forEach(form => {
            form.removeEventListener('submit', handleFormSubmit); // Prevent duplicate listeners
            form.addEventListener('submit', handleFormSubmit);
        });

        // Attach click listeners for modal buttons (Add New User, Edit User, Add New Token, Edit Token)
        element.querySelectorAll('button[data-action]').forEach(button => {
            button.removeEventListener('click', handleModalButtonClick); // Prevent duplicate listeners
            button.addEventListener('click', handleModalButtonClick);
        });

        // For the token creation form's token type select
        const tokenTypeSelect = element.querySelector('#token-type');
        if (tokenTypeSelect) {
            tokenTypeSelect.removeEventListener('change', window.toggleApiSelection); // Prevent duplicates
            tokenTypeSelect.addEventListener('change', window.toggleApiSelection);
            // Initial call to set correct state on page load
            window.toggleApiSelection();
        }

        // For the user form's password generate button
        const passwordGenerateButton = element.querySelector('button[onclick="generateRandomPassword()"]');
        if (passwordGenerateButton) {
            passwordGenerateButton.removeEventListener('click', window.generateRandomPassword); // Prevent duplicates
            passwordGenerateButton.addEventListener('click', window.generateRandomPassword);
        }

        // For the user form's access all APIs checkbox
        const accessAllApisCheckbox = element.querySelector('#access_all_apis');
        if (accessAllApisCheckbox) {
            accessAllApisCheckbox.removeEventListener('change', window.toggleApiSelection); // Prevent duplicates
            accessAllApisCheckbox.addEventListener('change', window.toggleApiSelection);
            // Initial call for dynamically loaded forms
            window.toggleApiSelection();
        }

        // Attach listener for modal close buttons (the 'X')
        element.querySelectorAll('button[onclick="closeModal()"]').forEach(button => {
            button.removeEventListener('click', window.closeModal); // Prevent duplicates
            button.addEventListener('click', window.closeModal);
        });

        const roleSelect = element.querySelector('#role');
        if (roleSelect) {
            roleSelect.removeEventListener('change', window.toggleApiSelection); // Prevent duplicates
            roleSelect.addEventListener('change', window.toggleApiSelection);
            // Initial call to set correct state on page load
            window.toggleApiSelection();
        }

        // Attach filter listeners for log tables
        attachFilterListeners(element);

        // Attach change listener for items per page select
        element.querySelectorAll('select[name="per_page"]').forEach(select => {
            select.removeEventListener('change', handlePerPageChange); // Prevent duplicate listeners
            select.addEventListener('change', handlePerPageChange);
        });
    }

    function handlePerPageChange(e) {
        const newPerPage = e.target.value;
        const currentUrl = currentPath; // Use currentPath from the SPA context
        const newUrl = window.updateQueryStringParameter(currentUrl, 'per_page', newPerPage);
        loadContent(newUrl);
    }

    function attachFilterListeners(element) {
        const filterInputs = element.querySelectorAll('th input[name$="_filter"], th select[name$="_filter"]');
        filterInputs.forEach(input => {
            input.removeEventListener('input', handleFilterChange); // For text inputs
            input.removeEventListener('change', handleFilterChange); // For select inputs

            input.addEventListener('input', handleFilterChange);
            input.addEventListener('change', handleFilterChange);
        });
    }

    let filterTimeout; // To debounce input events

    function handleFilterChange(e) {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
            let newPath = currentPath; // Start with the current path

            // Update log_type if it's a tab change (though tabs are handled by handleNavLinkClick)
            // This part might be redundant if tabs are handled separately, but keeping for safety
            const currentLogType = document.querySelector('#tabs option[selected]')?.dataset.path.split('log_type=')[1] || 'system';
            newPath = window.updateQueryStringParameter(newPath, 'log_type', currentLogType);

            // Collect all filter inputs and update newPath
            const filterInputs = document.querySelectorAll('th input[name$="_filter"], th select[name$="_filter"]');
            filterInputs.forEach(input => {
                if (input.value) {
                    newPath = window.updateQueryStringParameter(newPath, input.name, input.value);
                } else {
                    // If filter is cleared, remove it from the URL
                    newPath = window.updateQueryStringParameter(newPath, input.name, ''); // Pass empty string to remove
                }
            });

            // Ensure page is reset to 1 when filters change
            newPath = window.updateQueryStringParameter(newPath, 'page', 1);

            loadContent(newPath);
        }, 500); // Debounce for 500ms
    }

    // Handler for internal navigation links
    function handleNavLinkClick(e) {
        e.preventDefault();
        const targetPath = e.target.dataset.path;
        if (targetPath) {
            loadContent(targetPath);
        }
    }

    // Handler for modal buttons (Add New User, Edit User, Add New Token, Edit Token)
    function handleModalButtonClick(e) {
        const action = e.target.dataset.action;
        const userId = e.target.dataset.userId;
        const tokenId = e.target.dataset.tokenId;

        if (action === 'create-user') {
            window.openGenericModal('/admin/users/create-form');
        } else if (action === 'edit-user') {
            window.openGenericModal(`/admin/users/${userId}/edit-content`);
        } else if (action === 'create-token') {
            window.openGenericModal('/admin/token/create-form');
        } else if (action === 'edit-token') {
            window.openGenericModal(`/admin/token/${tokenId}/edit-content`);
        } else if (action === 'edit-api-script') {
            const scriptId = e.target.dataset.scriptId;
            window.openGenericModal(`/admin/api-scripts/${scriptId}/edit-content`);
        }
    }

    // Handle navigation clicks in the main header
    document.querySelectorAll('header nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            const targetPath = e.target.dataset.path;
            if (targetPath) {
                e.preventDefault(); // Only prevent default if data-path is present
                loadContent(targetPath);
            }
            // If no data-path, allow default link behavior (e.g., for logout)
        });
    });

    // Initial content load
    if (window.location.pathname.startsWith('/admin')) {
        loadContent(currentPath);
    }

    // Make closeModal globally available for the modal's close button
    window.closeModal = () => {
        genericModal.style.display = 'none';
        genericModalContent.innerHTML = ''; // Clear content
        // After closing modal, reload the current content
        loadContent(currentPath);
    };

    // Make a generic modal opener globally available
    window.openGenericModal = async (url) => {
        try {
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // Check for redirects
            if (response.redirected) {
                window.location.href = response.url; // Follow the redirect
                return; // Stop further processing
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const html = await response.text();
            genericModalContent.innerHTML = html;
            genericModal.style.display = 'flex';

            const codeBlock = genericModalContent.querySelector('pre code.language-json');
            if (codeBlock) {
                hljs.highlightElement(codeBlock);
            }
            // Re-attach event listeners for the form inside the modal
            attachEventListeners(genericModalContent);
        } catch (error) {
            console.error('Error loading form into modal:', error);
            showFlashMessage('Failed to load form.', 'danger');
        }
    };

    // Make generateRandomPassword and toggleApiSelection globally available
    window.generateRandomPassword = () => {
        const length = 12;
        const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+";
        let password = "";
        for (let i = 0, n = charset.length; i < length; ++i) {
            password += charset.charAt(Math.floor(Math.random() * n));
        }
        document.getElementById('password').value = password;
    };

    window.toggleApiSelection = () => {
        const roleSelect = document.getElementById('role');
        const accessAllApisCheckbox = document.getElementById('access_all_apis');
        const apiSelectionDiv = document.getElementById('api-selection');
        const accessAllApisContainer = accessAllApisCheckbox ? accessAllApisCheckbox.parentElement : null;

        if (roleSelect) { // We are in the user form
            if (roleSelect.value === 'admin') {
                if (accessAllApisContainer) accessAllApisContainer.style.display = 'none';
                if (apiSelectionDiv) apiSelectionDiv.style.display = 'none';
                if (accessAllApisCheckbox) accessAllApisCheckbox.checked = true; // Ensure it's checked for admins
            } else { // Role is 'user'
                if (accessAllApisContainer) accessAllApisContainer.style.display = 'flex';
                if (accessAllApisCheckbox && apiSelectionDiv) {
                    if (accessAllApisCheckbox.checked) {
                        apiSelectionDiv.style.display = 'none';
                    } else {
                        apiSelectionDiv.style.display = 'block';
                    }
                }
            }
        } else { // We are in the token form
            const tokenTypeSelect = document.getElementById('token-type');
            const tokenApiSelectionDiv = document.getElementById('api-selection');
            if (tokenTypeSelect && tokenApiSelectionDiv) {
                if (tokenTypeSelect.value === 'app') {
                    tokenApiSelectionDiv.style.display = 'block';
                } else {
                    tokenApiSelectionDiv.style.display = 'none';
                }
            }
        }
    };

    // Function to toggle visibility of API token
    window.toggleTokenVisibility = (element) => {
        const fullToken = element.dataset.fullToken;
        if (element.textContent.trim() === '********-****-****-****-************') {
            element.textContent = fullToken;
        } else {
            element.textContent = '********-****-****-****-************';
        }
    };

    // Function to update or add a query string parameter
    window.updateQueryStringParameter = function(uri, key, value) {
        var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
        var separator = uri.indexOf('?') !== -1 ? "&" : "?";
        if (uri.match(re)) {
            return uri.replace(re, '$1' + key + "=" + value + '$2');
        }
        else {
            return uri + separator + key + "=" + value;
        }
    };

    // Get elements
    const userMenuButton = document.getElementById('user-menu-button');
    const userDropdownMenu = document.getElementById('user-dropdown-menu');
    const changePasswordLink = document.getElementById('change-password-link');
    const changePasswordModal = document.getElementById('change-password-modal');
    const cancelChangePasswordButton = document.getElementById('cancel-change-password');
    const changePasswordForm = document.getElementById('change-password-form');

    // Toggle user dropdown menu
    if (userMenuButton && userDropdownMenu) {
        userMenuButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent click from propagating to document and closing immediately
            userDropdownMenu.classList.toggle('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (event) => {
            if (!userMenuButton.contains(event.target) && !userDropdownMenu.contains(event.target)) {
                userDropdownMenu.classList.add('hidden');
            }
        });
    }

    // Show change password modal
    if (changePasswordLink && changePasswordModal) {
        changePasswordLink.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent default link behavior
            userDropdownMenu.classList.add('hidden'); // Hide dropdown
            changePasswordModal.style.display = 'flex'; // Show modal
        });
    }

    // Hide change password modal
    if (cancelChangePasswordButton && changePasswordModal) {
        cancelChangePasswordButton.addEventListener('click', () => {
            changePasswordModal.style.display = 'none';
            changePasswordForm.reset(); // Clear form fields
        });

        // Close modal when clicking outside (on the overlay)
        changePasswordModal.addEventListener('click', (event) => {
            if (event.target === changePasswordModal) {
                changePasswordModal.style.display = 'none';
                changePasswordForm.reset();
            }
        });
    }

    // Handle change password form submission
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission

            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmNewPassword = document.getElementById('confirm-new-password').value;

            if (newPassword !== confirmNewPassword) {
                showNotification('Les nouveaux mots de passe ne correspondent pas.', 'error');
                return;
            }

            try {
                const response = await fetch('/admin/change_password', { // This endpoint needs to be created
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    showNotification(data.message, 'success');
                    changePasswordModal.style.display = 'none'; // Hide modal on success
                    changePasswordForm.reset(); // Clear form fields
                } else {
                    showNotification(data.message, 'error');
                }
            } catch (error) {
                console.error('Error changing password:', error);
                showNotification('Une erreur est survenue lors du changement de mot de passe.', 'error');
            }
        });
    }
});



function showNotification(message, type = 'info') {
    const container = document.getElementById('notifications-container');
    const notification = document.createElement('div');
    notification.classList.add('notification', type);
    notification.textContent = message;
    container.appendChild(notification);

    // Trigger reflow to enable transition
    void notification.offsetWidth;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
        notification.addEventListener('transitionend', () => notification.remove());
    }, 3000); // Notification disappears after 3 seconds
}