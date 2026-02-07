document.addEventListener('DOMContentLoaded', () => {
    // 1. Visits Tracking
    trackVisit();

    // 2. Download Form Handling
    const form = document.getElementById('downloadForm');
    if (form) {
        form.addEventListener('submit', handleDownload);
    }
});

async function trackVisit() {
    try {
        const response = await fetch('/api/stats/visit', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            const welcomeDiv = document.getElementById('visitorWelcome');
            const numSpan = document.getElementById('dailyVisitorNum');

            if (welcomeDiv && numSpan && data.visitor_number) {
                numSpan.textContent = getOrdinal(data.visitor_number);
                welcomeDiv.style.display = 'block';
            }
        }
    } catch (e) {
        console.error("Failed to track visit", e);
    }
}

function getOrdinal(n) {
    const s = ["th", "st", "nd", "rd"];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

async function handleDownload(e) {
    e.preventDefault();
    const btn = document.getElementById('downloadBtn');
    const msg = document.getElementById('message');

    // UI Loading State
    btn.disabled = true;
    btn.classList.add('btn-loading');
    msg.textContent = '';
    msg.className = 'message';

    const formData = new FormData(e.target);

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Trigger file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Try to get filename from header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'download.zip';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) filename = match[1];
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            msg.textContent = 'Download started!';
            msg.classList.add('success');

            // Update stats visually (optional, requires refresh usually)
        } else {
            const errorData = await response.json();
            msg.textContent = errorData.error || 'Download failed.';
            msg.classList.add('error');
        }
    } catch (err) {
        msg.textContent = 'Network error occurred.';
        msg.classList.add('error');
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.classList.remove('btn-loading');
    }
}
