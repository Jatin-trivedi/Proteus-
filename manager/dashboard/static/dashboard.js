// Global helper – you can add more here
console.log('JOCKY Dashboard loaded.');

// Helper to format timestamps
function formatDate(dateStr) {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
}

// Helper to truncate long strings
function truncate(str, len = 20) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len) + '...' : str;
}