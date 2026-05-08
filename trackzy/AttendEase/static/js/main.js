/**
 * Main JavaScript file for Department Attendance Management System
 * Handles global functionality, animations, and common UI interactions
 */

// Global application object
const AttendanceApp = {
    // Configuration
    config: {
        animationDuration: 400,
        toastDuration: 3000,
        chartColors: {
            primary: '#4361ee',
            success: '#2dce89',
            warning: '#fb6340',
            danger: '#f5365c',
            info: '#11cdef'
        }
    },

    // Initialize the application
    init() {
        this.initEventListeners();
        this.initAnimations();
        this.initTooltips();
        this.initDateTimeUpdater();
        this.handleFormValidation();
    },

    // Initialize global event listeners
    initEventListeners() {
        // Navigation active states
        this.updateActiveNavigation();

        // Auto-resize textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            this.autoResizeTextarea(textarea);
        });

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Handle form submissions with loading states
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmit(form, e);
            });
        });

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Handle responsive navigation
        this.initResponsiveNavigation();
    },

    // Initialize animations
    initAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.stat-card, .class-dashboard-card, .class-overview-card').forEach(card => {
            observer.observe(card);
        });

        // Add hover effects
        this.addHoverEffects();
    },

    // Initialize tooltips
    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Custom tooltip functionality for charts and data points
        this.initCustomTooltips();
    },

    // Update active navigation states
    updateActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    },

    // Auto-resize textarea
    autoResizeTextarea(textarea) {
        const resize = () => {
            textarea.style.height = 'auto';
            textarea.style.height = (textarea.scrollHeight + 2) + 'px';
        };

        textarea.addEventListener('input', resize);
        textarea.addEventListener('focus', resize);
        
        // Initial resize
        resize();
    },

    // Handle form validation
    handleFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');

        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });

        // Real-time validation
        document.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
        });
    },

    // Validate individual field
    validateField(field) {
        const isValid = field.checkValidity();
        const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                        field.parentNode.querySelector('.valid-feedback');

        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
    },

    // Handle form submission with loading states
    handleFormSubmit(form, event) {
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            const originalText = submitBtn.innerHTML;
            
            // Add loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';

            // Reset after 30 seconds (fallback)
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }, 30000);
        }
    },

    // Handle keyboard shortcuts
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + / for search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape key to close modals/dropdowns
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                modal?.hide();
            }
        }
    },

    // Initialize responsive navigation
    initResponsiveNavigation() {
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link:not(.dropdown-toggle)');

        if (navbarToggler && navbarCollapse) {
            // Close navbar when clicking a link (mobile)
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                        bootstrap.Collapse.getInstance(navbarCollapse)?.hide();
                    }
                });
            });

            // Close navbar when clicking outside
            document.addEventListener('click', (e) => {
                if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
                    if (navbarCollapse.classList.contains('show')) {
                        bootstrap.Collapse.getInstance(navbarCollapse)?.hide();
                    }
                }
            });
        }
    },

    // Add hover effects
    addHoverEffects() {
        // Card hover effects
        document.querySelectorAll('.card, .stat-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });

        // Button hover effects
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                if (!btn.disabled) {
                    btn.style.transform = 'translateY(-2px)';
                }
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translateY(0)';
            });
        });
    },

    // Initialize custom tooltips
    initCustomTooltips() {
        // Percentage badges
        document.querySelectorAll('.badge').forEach(badge => {
            if (badge.textContent.includes('%')) {
                badge.setAttribute('title', 'Attendance Percentage');
                badge.setAttribute('data-bs-toggle', 'tooltip');
            }
        });

        // Status indicators
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            const status = indicator.closest('.student-item')?.classList.contains('present') 
                ? 'Present' : 'Absent';
            indicator.setAttribute('title', status);
            indicator.setAttribute('data-bs-toggle', 'tooltip');
        });
    },

    // DateTime updater
    initDateTimeUpdater() {
        const updateDateTime = () => {
            const now = new Date();
            const dateElements = document.querySelectorAll('[data-datetime="current"]');
            
            dateElements.forEach(element => {
                const format = element.getAttribute('data-format') || 'full';
                let formattedDate;

                switch (format) {
                    case 'date':
                        formattedDate = now.toLocaleDateString();
                        break;
                    case 'time':
                        formattedDate = now.toLocaleTimeString();
                        break;
                    case 'full':
                    default:
                        formattedDate = now.toLocaleString();
                        break;
                }

                element.textContent = formattedDate;
            });
        };

        // Update immediately and then every minute
        updateDateTime();
        setInterval(updateDateTime, 60000);
    },

    // Utility functions
    utils: {
        // Format numbers
        formatNumber(num, decimals = 0) {
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(num);
        },

        // Format percentage
        formatPercentage(value, total) {
            if (total === 0) return '0%';
            return `${((value / total) * 100).toFixed(1)}%`;
        },

        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Throttle function
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            }
        },

        // Show toast notification
        showToast(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `toast-notification alert alert-${type}`;
            toast.textContent = message;
            
            // Add close button
            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.className = 'btn-close ms-2';
            closeBtn.addEventListener('click', () => {
                toast.classList.remove('show');
                setTimeout(() => document.body.removeChild(toast), 300);
            });
            
            toast.appendChild(closeBtn);
            document.body.appendChild(toast);

            // Show toast
            setTimeout(() => toast.classList.add('show'), 100);

            // Auto hide
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.classList.remove('show');
                    setTimeout(() => {
                        if (toast.parentNode) {
                            document.body.removeChild(toast);
                        }
                    }, 300);
                }
            }, duration);

            return toast;
        },

        // Copy to clipboard
        copyToClipboard(text) {
            if (navigator.clipboard) {
                return navigator.clipboard.writeText(text).then(() => {
                    this.showToast('Copied to clipboard!', 'success');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.opacity = '0';
                document.body.appendChild(textArea);
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    this.showToast('Copied to clipboard!', 'success');
                } catch (err) {
                    this.showToast('Failed to copy text', 'error');
                } finally {
                    document.body.removeChild(textArea);
                }
            }
        },

        // Generate unique ID
        generateId(prefix = 'id') {
            return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        },

        // Sanitize HTML
        sanitizeHTML(str) {
            const temp = document.createElement('div');
            temp.textContent = str;
            return temp.innerHTML;
        },

        // Get URL parameters
        getUrlParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        },

        // Set URL parameter without reload
        setUrlParam(param, value) {
            const url = new URL(window.location);
            url.searchParams.set(param, value);
            window.history.pushState({}, '', url);
        },

        // Remove URL parameter
        removeUrlParam(param) {
            const url = new URL(window.location);
            url.searchParams.delete(param);
            window.history.pushState({}, '', url);
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    AttendanceApp.init();
});

// Global utility functions for backward compatibility
window.showToast = AttendanceApp.utils.showToast.bind(AttendanceApp.utils);
window.formatPercentage = AttendanceApp.utils.formatPercentage.bind(AttendanceApp.utils);
window.debounce = AttendanceApp.utils.debounce.bind(AttendanceApp.utils);

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AttendanceApp;
}
