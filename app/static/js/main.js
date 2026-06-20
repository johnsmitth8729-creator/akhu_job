// Al-Khwarizmi University Recruitment Portal - General JS

// Change Language segment in URL
function changeLanguage(langCode) {
    const path = window.location.pathname;
    const parts = path.split('/');
    if (parts.length > 1 && ['en', 'uz'].includes(parts[1])) {
        parts[1] = langCode;
        window.location.pathname = parts.join('/');
    } else {
        // Fallback if URL is root
        window.location.pathname = `/${langCode}` + path;
    }
}

// Theme Toggle Functionality
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeToggleIcon');
    if (!themeIcon) return;
    
    if (theme === 'light') {
        themeIcon.className = 'bi bi-sun-fill';
    } else {
        themeIcon.className = 'bi bi-moon-stars-fill';
    }
}

// Run immediately to set initial icon state on load
document.addEventListener('DOMContentLoaded', function() {
    const activeTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    updateThemeIcon(activeTheme);
    
    // Automatically fade out flash alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Check if bootstrap alert object exists and close it
            if (window.bootstrap && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }
        }, 5000);
    });
});
