function copyToClipboard() {
    const shortUrl = document.getElementById('shortUrl');
    shortUrl.select();
    shortUrl.setSelectionRange(0, 99999);
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopyFeedback(event.target);
        }
    } catch (err) {
        // Fallback for modern browsers
        navigator.clipboard.writeText(shortUrl.value).then(() => {
            showCopyFeedback(event.target);
        });
    }
}

function showCopyFeedback(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i> Copied!';
    button.classList.remove('btn-outline-success');
    button.classList.add('btn-success');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('btn-success');
        button.classList.add('btn-outline-success');
    }, 2000);
}

function copyShortUrl(url) {
    navigator.clipboard.writeText(url).then(() => {
        // Simple alert for feedback
        alert('URL copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

// API example usage
async function shortenWithAPI(url, customAlias = null) {
    try {
        const response = await fetch('/api/shorten', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                custom_alias: customAlias
            })
        });
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: 'Failed to connect to server' };
    }
}

// Add some interactive features
document.addEventListener('DOMContentLoaded', function() {
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
            }
        });
    });
});