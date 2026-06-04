// Hospital Management System JavaScript

// Global variables
let currentUser = null;
let hospitalConfig = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

// Initialize application
function initializeApp() {
    console.log('Hospital Management System initialized');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize barcode scanner
    initializeBarcodeScanner();
}

// Update current time display
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

// Form validation
function initializeFormValidation() {
    // Add custom validation styles
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Mobile number validation
function validateMobileNumber(mobile) {
    const pattern = /^[6-9]\d{9}$/;
    return pattern.test(mobile);
}

// Patient ID validation
function validatePatientId(patientId) {
    const pattern = /^P\d{8}\d{4}$/;
    return pattern.test(patientId);
}

// Show loading spinner
function showLoading(element) {
    if (element) {
        element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        element.disabled = true;
    }
}

// Hide loading spinner
function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

// Show alert message
function showAlert(message, type = 'info', container = null) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const targetContainer = container || document.querySelector('.container-fluid');
    if (targetContainer) {
        targetContainer.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = targetContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// API request helper
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN');
}

// Format time
function formatTime(time) {
    return new Date(time).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Print functionality
function printSlip(slipId) {
    const printWindow = window.open(`/api/v1/slips/${slipId}/print`, '_blank');
    printWindow.onload = function() {
        printWindow.print();
        printWindow.close();
    };
}

// Barcode scanner initialization
function initializeBarcodeScanner() {
    // Check if barcode scanner is available
    if ('BarcodeDetector' in window) {
        console.log('Barcode scanner available');
        // Initialize barcode scanner functionality
    } else {
        console.log('Barcode scanner not available');
    }
}

// Search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function(e) {
            const query = e.target.value.trim();
            if (query.length >= 3) {
                performSearch(query, e.target.dataset.searchType);
            }
        }, 300));
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Perform search
async function performSearch(query, searchType) {
    try {
        const response = await apiRequest(`/api/v1/search?q=${encodeURIComponent(query)}&type=${searchType}`);
        displaySearchResults(response.results, searchType);
    } catch (error) {
        console.error('Search failed:', error);
        showAlert('Search failed. Please try again.', 'danger');
    }
}

// Display search results
function displaySearchResults(results, searchType) {
    const resultsContainer = document.getElementById(`${searchType}-results`);
    if (!resultsContainer) return;
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="text-muted">No results found</div>';
        return;
    }
    
    let html = '';
    results.forEach(result => {
        html += `
            <div class="search-result-item p-2 border-bottom" data-id="${result.id}">
                <div class="fw-bold">${result.name}</div>
                <div class="text-muted small">${result.details}</div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    
    // Add click handlers
    resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function() {
            selectSearchResult(this.dataset.id, searchType);
        });
    });
}

// Select search result
function selectSearchResult(id, searchType) {
    console.log(`Selected ${searchType} with ID: ${id}`);
    // Implement selection logic based on search type
}

// Export functions for global use
window.HospitalMS = {
    showAlert,
    showLoading,
    hideLoading,
    apiRequest,
    formatCurrency,
    formatDate,
    formatTime,
    printSlip,
    validateMobileNumber,
    validatePatientId
};