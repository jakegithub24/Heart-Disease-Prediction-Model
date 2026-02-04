document.addEventListener('DOMContentLoaded', function () {
    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';

    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    // Theme toggle event
    themeToggle.addEventListener('click', function () {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        // Smooth transition
        document.documentElement.style.transition = 'all 0.3s ease';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        updateThemeIcon(newTheme);

        // Remove transition after animation
        setTimeout(() => {
            document.documentElement.style.transition = '';
        }, 300);
    });

    function updateThemeIcon(theme) {
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            themeToggle.setAttribute('title', 'Switch to light mode');
        } else {
            icon.className = 'fas fa-moon';
            themeToggle.setAttribute('title', 'Switch to dark mode');
        }
    }

    // Fill Example Values
    const fillExampleBtn = document.getElementById('fillExample');
    const clearFormBtn = document.getElementById('clearForm');

    if (fillExampleBtn) {
        fillExampleBtn.addEventListener('click', function (e) {
            e.preventDefault();

            // Get all input fields
            const inputs = document.querySelectorAll('.feature-input-group input');
            const exampleValues = fillExampleBtn.dataset.example?.split(',') || [];

            inputs.forEach((input, index) => {
                if (exampleValues[index]) {
                    input.value = exampleValues[index].trim();
                    // Add animation
                    input.classList.add('filled-example');
                    setTimeout(() => {
                        input.classList.remove('filled-example');
                    }, 1000);
                }
            });

            // Show feedback
            showToast('Example values filled successfully!', 'success');
        });
    }

    if (clearFormBtn) {
        clearFormBtn.addEventListener('click', function (e) {
            e.preventDefault();

            // Clear all input fields
            document.querySelectorAll('.feature-input-group input').forEach(input => {
                input.value = '';
                input.classList.add('cleared');
                setTimeout(() => {
                    input.classList.remove('cleared');
                }, 500);
            });

            // Clear textarea
            const textarea = document.querySelector('textarea[name="raw_input"]');
            if (textarea) textarea.value = '';

            showToast('Form cleared!', 'info');
        });
    }

    // Form Submission Animation
    const predictForm = document.getElementById('predictForm');
    if (predictForm) {
        predictForm.addEventListener('submit', function (e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            // Disable button and show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Analyzing...
      `;

            // Add loading animation to form
            this.classList.add('processing');

            // Simulate processing animation
            const inputs = this.querySelectorAll('.form-control');
            inputs.forEach((input, index) => {
                setTimeout(() => {
                    input.classList.add('processing-input');
                }, index * 100);
            });

            // Re-enable after 3 seconds (in case of error)
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                predictForm.classList.remove('processing');
                inputs.forEach(input => input.classList.remove('processing-input'));
            }, 3000);
        });
    }

    // Animate elements on scroll
    function animateOnScroll() {
        const elements = document.querySelectorAll('.fade-in');

        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;

            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('animated');
            }
        });
    }

    // Initialize scroll animation
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run once on load

    // Auto-format feature inputs
    const featureInputs = document.querySelectorAll('.feature-input');
    featureInputs.forEach(input => {
        input.addEventListener('input', function (e) {
            // Remove non-numeric characters except decimal point
            let value = this.value.replace(/[^0-9.]/g, '');

            // Ensure only one decimal point
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }

            this.value = value;

            // Visual feedback
            if (value) {
                this.parentElement.classList.add('has-value');
            } else {
                this.parentElement.classList.remove('has-value');
            }
        });

        // Focus animation
        input.addEventListener('focus', function () {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function () {
            this.parentElement.classList.remove('focused');
        });
    });

    // Copy to clipboard functionality
    const copyExampleBtn = document.getElementById('copyExample');
    if (copyExampleBtn) {
        copyExampleBtn.addEventListener('click', function () {
            const exampleText = this.dataset.example;
            navigator.clipboard.writeText(exampleText)
                .then(() => {
                    const originalHTML = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    this.classList.add('copied');

                    setTimeout(() => {
                        this.innerHTML = originalHTML;
                        this.classList.remove('copied');
                    }, 2000);

                    showToast('Example copied to clipboard!', 'success');
                })
                .catch(err => {
                    showToast('Failed to copy to clipboard', 'error');
                });
        });
    }

    // Toast notification function
    function showToast(message, type = 'info') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast-container');
        existingToasts.forEach(toast => toast.remove());

        // Create toast container
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast show align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

        toastContainer.appendChild(toast);
        document.body.appendChild(toastContainer);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toastContainer.remove();
            }, 300);
        }, 3000);
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
});