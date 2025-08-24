// Escola Sol Maior - Main JavaScript Functions

(function() {
    'use strict';

    // DOM Content Loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
    });

    function initializeApp() {
        // Initialize all components
        initializeTooltips();
        initializePopovers();
        initializeForms();
        initializeTableSearch();
        initializeAnimations();
        initializeNotifications();
        initializePhoneMasks();
        initializeCurrencyMasks();
        
        // Add fade-in animation to main content
        document.body.classList.add('fade-in');
    }

    // Initialize Bootstrap tooltips
    function initializeTooltips() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize Bootstrap popovers
    function initializePopovers() {
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Form enhancements
    function initializeForms() {
        // Add floating labels effect
        const formFloatingInputs = document.querySelectorAll('.form-floating input, .form-floating textarea');
        formFloatingInputs.forEach(function(input) {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });
        });

        // Form validation feedback
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });

        // Auto-resize textareas
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(function(textarea) {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        });
    }

    // Table search functionality
    function initializeTableSearch() {
        const searchInputs = document.querySelectorAll('[data-table-search]');
        searchInputs.forEach(function(input) {
            const tableId = input.getAttribute('data-table-search');
            const table = document.getElementById(tableId);
            
            if (table) {
                input.addEventListener('keyup', function() {
                    filterTable(table, this.value);
                });
            }
        });
    }

    function filterTable(table, searchTerm) {
        const rows = table.querySelectorAll('tbody tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(function(row) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }

    // Animation utilities
    function initializeAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                }
            });
        }, observerOptions);

        // Observe elements with animation class
        const animateElements = document.querySelectorAll('.animate-on-scroll');
        animateElements.forEach(function(el) {
            observer.observe(el);
        });
    }

    // Notification system
    function initializeNotifications() {
        // Auto-hide alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                if (bsAlert) {
                    bsAlert.close();
                }
            }, 5000);
        });
    }

    // Phone number masking
    function initializePhoneMasks() {
        const phoneInputs = document.querySelectorAll('input[type="tel"], input[placeholder*="phone"], input[placeholder*="telefone"]');
        phoneInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                
                if (value.length <= 10) {
                    value = value.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
                } else {
                    value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
                }
                
                e.target.value = value;
            });
        });
    }

    // Currency masking
    function initializeCurrencyMasks() {
        const currencyInputs = document.querySelectorAll('input[data-mask="currency"]');
        currencyInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                value = (value / 100).toFixed(2);
                value = value.replace('.', ',');
                value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
                e.target.value = 'R$ ' + value;
            });
        });
    }

    // Utility functions
    window.SolMaior = {
        // Show loading spinner
        showLoading: function(element) {
            const originalContent = element.innerHTML;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Carregando...';
            element.disabled = true;
            
            return {
                hide: function() {
                    element.innerHTML = originalContent;
                    element.disabled = false;
                }
            };
        },

        // Show toast notification
        showToast: function(message, type = 'info') {
            const toastContainer = document.getElementById('toast-container') || createToastContainer();
            const toastId = 'toast-' + Date.now();
            
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.id = toastId;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;
            
            toastContainer.appendChild(toast);
            
            const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
            bsToast.show();
            
            toast.addEventListener('hidden.bs.toast', function() {
                toast.remove();
            });
        },

        // Confirm dialog
        confirm: function(message, callback) {
            if (confirm(message)) {
                callback();
            }
        },

        // Format currency
        formatCurrency: function(value) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        },

        // Format phone
        formatPhone: function(phone) {
            const cleaned = phone.replace(/\D/g, '');
            if (cleaned.length === 10) {
                return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
            } else if (cleaned.length === 11) {
                return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
            }
            return phone;
        },

        // AJAX helper
        ajax: function(url, options = {}) {
            const defaults = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            };

            options = Object.assign(defaults, options);

            return fetch(url, options)
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .catch(function(error) {
                    console.error('AJAX Error:', error);
                    SolMaior.showToast('Erro na requisição', 'danger');
                    throw error;
                });
        },

        // Validate form
        validateForm: function(form) {
            let isValid = true;
            const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
            
            inputs.forEach(function(input) {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            return isValid;
        }
    };

    // Create toast container if it doesn't exist
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '11';
        document.body.appendChild(container);
        return container;
    }

    // Global error handler
    window.addEventListener('error', function(e) {
        console.error('Global error:', e.error);
        if (window.SolMaior) {
            SolMaior.showToast('Ocorreu um erro inesperado', 'danger');
        }
    });

    // Service Worker registration (if available)
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/static/sw.js')
                .then(function(registration) {
                    console.log('SW registered: ', registration);
                })
                .catch(function(registrationError) {
                    console.log('SW registration failed: ', registrationError);
                });
        });
    }

})();

// Specific page functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Dashboard specific code
    if (document.body.classList.contains('dashboard-page')) {
        initializeDashboard();
    }

    // Forms specific code
    if (document.querySelector('form')) {
        initializeFormSpecific();
    }

    // Tables specific code
    if (document.querySelector('.table')) {
        initializeTableSpecific();
    }
});

function initializeDashboard() {
    // Dashboard charts and widgets can be initialized here
    console.log('Dashboard initialized');
}

function initializeFormSpecific() {
    // Form-specific enhancements
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(function(input) {
        addPasswordToggle(input);
    });
}

function addPasswordToggle(input) {
    const wrapper = document.createElement('div');
    wrapper.className = 'input-group';
    
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    
    const button = document.createElement('button');
    button.className = 'btn btn-outline-secondary';
    button.type = 'button';
    button.innerHTML = '<i class="fas fa-eye"></i>';
    
    button.addEventListener('click', function() {
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
    });
    
    wrapper.appendChild(button);
}

function initializeTableSpecific() {
    // Table-specific enhancements
    const tables = document.querySelectorAll('.table');
    tables.forEach(function(table) {
        // Add row selection functionality if needed
        addTableRowSelection(table);
    });
}

function addTableRowSelection(table) {
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(function(row) {
        row.addEventListener('click', function(e) {
            if (!e.target.closest('button, a, input')) {
                row.classList.toggle('table-active');
            }
        });
    });
}
