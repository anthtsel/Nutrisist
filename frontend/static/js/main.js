// Form Validation
document.addEventListener('DOMContentLoaded', function() {
    // Password confirmation validation
    const passwordConfirm = document.getElementById('confirm_password');
    if (passwordConfirm) {
        passwordConfirm.addEventListener('input', function() {
            const password = document.getElementById('password');
            if (this.value !== password.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Flash message handling
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 3000);
    });

    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// Activity data updates
function updateActivityData() {
    // This would be replaced with actual API calls
    const activityCards = document.querySelectorAll('.activity-card');
    activityCards.forEach(function(card) {
        const value = card.querySelector('.activity-value');
        const randomValue = Math.floor(Math.random() * 1000);
        value.textContent = randomValue;
    });
}

// Set up periodic updates (every 5 minutes)
setInterval(updateActivityData, 300000); 