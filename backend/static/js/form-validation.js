document.addEventListener('DOMContentLoaded', function() {
    // Common patterns for validation
    const patterns = {
        username: /^[A-Za-z0-9_-]{3,64}$/,
        email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
        password: {
            minLength: 8,
            maxLength: 128,
            hasUpperCase: /[A-Z]/,
            hasLowerCase: /[a-z]/,
            hasNumbers: /[0-9]/,
            hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/
        }
    };

    // Function to sanitize input
    function sanitizeInput(input) {
        return input.replace(/<[^>]*>/g, '') // Remove HTML tags
                   .replace(/[^\x20-\x7E]/g, '') // Remove non-printable characters
                   .trim(); // Remove leading/trailing whitespace
    }

    // Function to validate password
    function validatePassword(password) {
        const errors = [];
        
        if (password.length < patterns.password.minLength) {
            errors.push(`Password must be at least ${patterns.password.minLength} characters long`);
        }
        if (password.length > patterns.password.maxLength) {
            errors.push(`Password must not exceed ${patterns.password.maxLength} characters`);
        }
        if (!patterns.password.hasUpperCase.test(password)) {
            errors.push('Password must contain at least one uppercase letter');
        }
        if (!patterns.password.hasLowerCase.test(password)) {
            errors.push('Password must contain at least one lowercase letter');
        }
        if (!patterns.password.hasNumbers.test(password)) {
            errors.push('Password must contain at least one number');
        }
        if (!patterns.password.hasSpecialChar.test(password)) {
            errors.push('Password must contain at least one special character');
        }
        
        return errors;
    }

    // Function to show validation feedback
    function showFeedback(input, isValid, message) {
        const feedback = input.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            const div = document.createElement('div');
            div.className = isValid ? 'valid-feedback' : 'invalid-feedback';
            input.parentNode.appendChild(div);
        }
        
        input.classList.toggle('is-valid', isValid);
        input.classList.toggle('is-invalid', !isValid);
        
        if (feedback) {
            feedback.textContent = message;
        }
    }

    // Real-time validation for username
    document.querySelectorAll('input[name="username"]').forEach(input => {
        input.addEventListener('input', function() {
            const sanitized = sanitizeInput(this.value);
            this.value = sanitized;
            
            const isValid = patterns.username.test(sanitized);
            showFeedback(this, isValid, isValid ? 'Username is valid' : 'Username must be 3-64 characters long and can only contain letters, numbers, underscores, and hyphens');
        });
    });

    // Real-time validation for email
    document.querySelectorAll('input[name="email"]').forEach(input => {
        input.addEventListener('input', function() {
            const sanitized = sanitizeInput(this.value.toLowerCase());
            this.value = sanitized;
            
            const isValid = patterns.email.test(sanitized);
            showFeedback(this, isValid, isValid ? 'Email is valid' : 'Please enter a valid email address');
        });
    });

    // Real-time validation for password
    document.querySelectorAll('input[type="password"]').forEach(input => {
        input.addEventListener('input', function() {
            const errors = validatePassword(this.value);
            const isValid = errors.length === 0;
            showFeedback(this, isValid, isValid ? 'Password meets requirements' : errors.join(', '));
        });
    });

    // Form submission validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Validate all inputs before submission
            this.querySelectorAll('input').forEach(input => {
                const value = sanitizeInput(input.value);
                
                if (input.name === 'username' && !patterns.username.test(value)) {
                    isValid = false;
                }
                else if (input.name === 'email' && !patterns.email.test(value)) {
                    isValid = false;
                }
                else if (input.type === 'password') {
                    const errors = validatePassword(value);
                    if (errors.length > 0) {
                        isValid = false;
                    }
                }
            });
            
            // Check if passwords match in registration/reset forms
            const password1 = this.querySelector('input[name="password"]');
            const password2 = this.querySelector('input[name="password2"]');
            if (password1 && password2 && password1.value !== password2.value) {
                isValid = false;
                showFeedback(password2, false, 'Passwords do not match');
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
}); 