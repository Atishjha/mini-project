// frontend/js/auth.js

// Auth state
let currentUser = null;
let authToken = localStorage.getItem('authToken');

// Check if user is logged in on page load
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        validateToken();
    } else {
        updateUIBasedOnAuth();
    }
});

// Validate token with backend
async function validateToken() {
    try {
        const response = await fetch('http://localhost:5000/api/auth/profile', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const userData = await response.json();
            currentUser = userData;
            updateUIBasedOnAuth();
            showToast(`Welcome back, ${userData.username}!`, 'success');
        } else {
            // Token invalid
            logout();
        }
    } catch (error) {
        console.error('Token validation error:', error);
        logout();
    }
}

// Update UI based on authentication state
function updateUIBasedOnAuth() {
    const authButtons = document.getElementById('auth-buttons');
    const userMenu = document.getElementById('user-menu');
    const userInfoCard = document.getElementById('user-info-card');
    const operatorActions = document.getElementById('operator-actions');
    const adminActions = document.getElementById('admin-actions');
    
    if (currentUser) {
        // User is logged in
        authButtons.style.display = 'none';
        userMenu.style.display = 'block';
        userInfoCard.style.display = 'block';
        
        // Update user info
        document.getElementById('username-display').textContent = currentUser.username;
        document.getElementById('user-name').textContent = currentUser.username;
        document.getElementById('user-role').innerHTML = `Role: <span class="badge bg-${getRoleBadgeColor(currentUser.role)}">${currentUser.role}</span>`;
        
        // Show/hide role-based actions
        const permissions = currentUser.permissions || {};
        
        if (currentUser.role === 'admin' || currentUser.role === 'operator') {
            operatorActions.style.display = 'block';
        } else {
            operatorActions.style.display = 'none';
        }
        
        if (currentUser.role === 'admin') {
            adminActions.style.display = 'block';
        } else {
            adminActions.style.display = 'none';
        }
        
    } else {
        // User is logged out
        authButtons.style.display = 'block';
        userMenu.style.display = 'none';
        userInfoCard.style.display = 'none';
        operatorActions.style.display = 'none';
        adminActions.style.display = 'none';
    }
}

// Get badge color based on role
function getRoleBadgeColor(role) {
    const colors = {
        'admin': 'danger',
        'operator': 'warning',
        'field_responder': 'success',
        'viewer': 'info',
        'public': 'secondary'
    };
    return colors[role] || 'secondary';
}

// Login function
async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        showToast('Please enter username and password', 'error');
        return;
    }
    
    try {
        showLoading('Logging in...');
        
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            
            // Store token
            localStorage.setItem('authToken', authToken);
            
            // Update UI
            updateUIBasedOnAuth();
            
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            
            showToast(`Welcome, ${currentUser.username}!`, 'success');
            
            // Reset form
            document.getElementById('login-form').reset();
            
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showToast('Connection error', 'error');
    } finally {
        hideLoading();
    }
}

// Register function
async function register() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    const phone = document.getElementById('register-phone').value;
    const department = document.getElementById('register-department').value;
    
    // Validation
    if (!username || !email || !password) {
        showToast('Please fill all required fields', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    if (password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }
    
    try {
        showLoading('Creating account...');
        
        const response = await fetch('http://localhost:5000/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                email,
                password,
                phone,
                department
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Registration successful! Please login.', 'success');
            
            // Close register modal
            bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
            
            // Reset form
            document.getElementById('register-form').reset();
            
            // Show login modal
            setTimeout(() => showLoginModal(), 500);
            
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Connection error', 'error');
    } finally {
        hideLoading();
    }
}

// Logout function
function logout() {
    // Clear stored data
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    
    // Update UI
    updateUIBasedOnAuth();
    
    showToast('Logged out successfully', 'info');
}

// Show profile
async function showProfile() {
    if (!currentUser) {
        showToast('Please login first', 'warning');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/auth/profile', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const profile = await response.json();
            
            // Update profile modal
            document.getElementById('profile-username').textContent = profile.username;
            document.getElementById('profile-email').textContent = profile.email;
            document.getElementById('profile-role').innerHTML = `<span class="badge bg-${getRoleBadgeColor(profile.role)}">${profile.role}</span>`;
            document.getElementById('profile-department').textContent = profile.department || '-';
            document.getElementById('profile-phone').textContent = profile.phone || '-';
            
            // Format dates
            const createdDate = profile.created_at ? new Date(profile.created_at).toLocaleDateString() : '-';
            const lastLogin = profile.last_login ? new Date(profile.last_login).toLocaleString() : '-';
            
            document.getElementById('profile-created').textContent = createdDate;
            document.getElementById('profile-last-login').textContent = lastLogin;
            
            // Show permissions
            const permissionsDiv = document.getElementById('profile-permissions');
            const permissions = profile.permissions || {};
            
            let permissionsHtml = '<div class="list-group">';
            for (const [perm, value] of Object.entries(permissions)) {
                permissionsHtml += `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        ${perm.replace(/_/g, ' ')}
                        <span class="badge bg-${value ? 'success' : 'secondary'}">${value ? '✓' : '✗'}</span>
                    </div>
                `;
            }
            permissionsHtml += '</div>';
            
            permissionsDiv.innerHTML = permissionsHtml;
            
            // Show modal
            new bootstrap.Modal(document.getElementById('profileModal')).show();
        }
        
    } catch (error) {
        console.error('Profile error:', error);
        showToast('Failed to load profile', 'error');
    }
}

// Check if user has permission
function hasPermission(permission) {
    if (!currentUser || !currentUser.permissions) {
        return false;
    }
    return currentUser.permissions[permission] || false;
}

// Check if user has role
function hasRole(role) {
    if (!currentUser) {
        return false;
    }
    if (Array.isArray(role)) {
        return role.includes(currentUser.role);
    }
    return currentUser.role === role;
}

// Show login modal
function showLoginModal() {
    new bootstrap.Modal(document.getElementById('loginModal')).show();
}

// Show register modal
function showRegisterModal() {
    new bootstrap.Modal(document.getElementById('registerModal')).show();
}

// Show user management (admin only)
function showUserManagement() {
    if (!hasRole('admin')) {
        showToast('Access denied. Admin only.', 'error');
        return;
    }
    showToast('User management - Coming soon', 'info');
}

// Show system config (admin only)
function showSystemConfig() {
    if (!hasRole('admin')) {
        showToast('Access denied. Admin only.', 'error');
        return;
    }
    showToast('System configuration - Coming soon', 'info');
}

// Show dashboard (role-based)
function showDashboard() {
    if (!currentUser) {
        showToast('Please login first', 'warning');
        return;
    }
    
    if (hasRole(['admin', 'operator', 'viewer'])) {
        showAnalytics();
    } else {
        showToast('You do not have access to analytics', 'error');
    }
}

// Make functions globally available
window.showLoginModal = showLoginModal;
window.showRegisterModal = showRegisterModal;
window.login = login;
window.register = register;
window.logout = logout;
window.showProfile = showProfile;
window.showUserManagement = showUserManagement;
window.showSystemConfig = showSystemConfig;
window.showDashboard = showDashboard;
window.hasPermission = hasPermission;
window.hasRole = hasRole;