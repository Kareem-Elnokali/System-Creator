/* Django Admin-inspired JavaScript for MFA System Creator */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.messagelist li');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.delete-button, .btn-danger');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Table row hover effects
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'var(--selected-bg)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.style.borderColor = 'var(--error-fg)';
                    isValid = false;
                } else {
                    field.style.borderColor = 'var(--border-color)';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
        });
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
        }
    }

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('table tbody tr');
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Bulk actions
    const selectAllCheckbox = document.getElementById('select-all');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(function(checkbox) {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBulkActions();
        });
    }
    
    itemCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', updateBulkActions);
    });
    
    function updateBulkActions() {
        const checkedBoxes = document.querySelectorAll('.item-checkbox:checked');
        const bulkActions = document.querySelector('.bulk-actions');
        
        if (bulkActions) {
            if (checkedBoxes.length > 0) {
                bulkActions.style.display = 'block';
                bulkActions.querySelector('.selected-count').textContent = checkedBoxes.length;
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }

    // AJAX for quick actions
    function performAjaxAction(url, data, successCallback) {
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                successCallback(data);
                showMessage('Action completed successfully', 'success');
            } else {
                showMessage(data.error || 'Action failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred', 'error');
        });
    }

    // Quick tenant actions
    const tenantActions = document.querySelectorAll('.tenant-action');
    tenantActions.forEach(function(button) {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const tenantId = this.dataset.tenantId;
            
            if (confirm(`Are you sure you want to ${action} this tenant?`)) {
                performAjaxAction('/api/tenant-action/', {
                    action: action,
                    tenant_id: tenantId
                }, function(data) {
                    location.reload();
                });
            }
        });
    });

    // Show messages
    function showMessage(text, type) {
        const messageList = document.querySelector('.messagelist') || createMessageList();
        const message = document.createElement('li');
        message.className = type;
        message.textContent = text;
        messageList.appendChild(message);
        
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    }

    function createMessageList() {
        const messageList = document.createElement('ul');
        messageList.className = 'messagelist';
        const content = document.getElementById('content');
        content.insertBefore(messageList, content.firstChild);
        return messageList;
    }

    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Charts initialization (if Chart.js is loaded)
    if (typeof Chart !== 'undefined') {
        // Usage trends chart
        const usageChart = document.getElementById('usage-chart');
        if (usageChart) {
            new Chart(usageChart, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Authentications',
                        data: [12, 19, 3, 5, 2, 3],
                        borderColor: 'var(--primary)',
                        backgroundColor: 'var(--primary)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Plan distribution chart
        const planChart = document.getElementById('plan-chart');
        if (planChart) {
            new Chart(planChart, {
                type: 'doughnut',
                data: {
                    labels: ['Free', 'Basic', 'Premium', 'Enterprise'],
                    datasets: [{
                        data: [45, 30, 20, 5],
                        backgroundColor: [
                            '#79aec8',
                            '#417690',
                            '#2c5f7a',
                            '#1a4d66'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }
});
