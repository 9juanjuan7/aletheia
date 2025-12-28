const API_URL = 'http://localhost:5000';

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'analyze') {
        analyzeArticle(message.url, message.title);
    }
});

async function analyzeArticle(url, title) {
    // Show loading state
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    try {
        // Call backend API
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, title })
        });

        const data = await response.json();

        // Display results
        displayResults(data, title, url);

    } catch (error) {
        console.error('Error analyzing article:', error);
        document.getElementById('loading').innerHTML = `
            <p>⚠️ Error connecting to Aletheia API.</p>
            <p style="font-size: 12px;">Make sure the backend is running on port 5000.</p>
        `;
    }
}

function displayResults(data, title, url) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';

    // Article info
    document.getElementById('article-title').textContent = title;
    const domain = new URL(url).hostname;
    document.getElementById('article-source').textContent = domain;

    // Main source credibility
    displayCredibilityScore(data.main_publication);
    displayFundingInfo(data.main_publication);
    displayFlags(data.main_publication);

    // Counter-perspective
    displayCounterPerspective(data.counter_perspective, data.analysis);

    // Analysis warning
    displayAnalysisWarning(data.analysis);

    // Myth detection
    displayMythDetection(data.myths);

    // Missing context
    displayMissingContext(data.missing_context);
}

function displayCredibilityScore(publication) {
    const container = document.getElementById('credibility-score');
    
    if (!publication) {
        container.innerHTML = '<p>ℹ️ Publication not in database</p>';
        return;
    }

    const score = publication.credibility_score || 0;
    const name = publication.name || publication.domain;
    
    let scoreClass = 'low';
    let scoreEmoji = '🔴';
    if (score >= 7) {
        scoreClass = 'high';
        scoreEmoji = '🟢';
    } else if (score >= 5) {
        scoreClass = 'medium';
        scoreEmoji = '🟡';
    }

    container.innerHTML = `
        <div class="credibility-badge credibility-${scoreClass}">
            ${scoreEmoji} Credibility: ${score}/10
        </div>
        <p style="margin: 8px 0 0 0; font-size: 13px;"><strong>${name}</strong></p>
        ${publication.credibility_explanation ? 
            `<p style="margin: 4px 0 0 0; font-size: 12px; color: #7f8c8d;">${publication.credibility_explanation}</p>` : ''}
    `;
}

function displayFundingInfo(publication) {
    const container = document.getElementById('funding-info');
    
    if (!publication) return;

    let html = '<div style="margin-top: 12px;">';

    // Ownership
    if (publication.ownership && publication.ownership !== 'Unknown') {
        html += `
            <div class="info-item">
                <span class="info-label">🏢 Owner:</span> ${publication.ownership}
            </div>
        `;
    }

    // Funding sources
    if (publication.funding_sources && publication.funding_sources.length > 0) {
        html += `
            <div class="info-item">
                <span class="info-label">💰 Funding:</span> ${publication.funding_sources.join(', ')}
            </div>
        `;
    }

    // Conflicts of interest
    if (publication.conflicts_of_interest && publication.conflicts_of_interest.length > 0) {
        html += `<div class="conflict">
            <strong>⚠️ Conflicts of Interest:</strong><br>
            ${publication.conflicts_of_interest.map(c => `• ${c}`).join('<br>')}
        </div>`;
    }

    // Funding transparency
    if (publication.funding_transparency) {
        const transparency = publication.funding_transparency;
        const transparencyEmoji = transparency === 'high' ? '✅' : transparency === 'medium' ? '⚠️' : '🚫';
        html += `
            <div class="info-item">
                <span class="info-label">${transparencyEmoji} Transparency:</span> ${transparency}
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

function displayFlags(publication) {
    const redContainer = document.getElementById('red-flags');
    const greenContainer = document.getElementById('green-flags');

    // Red flags
    if (publication.red_flags && publication.red_flags.length > 0) {
        redContainer.innerHTML = `
            <div class="conflict" style="margin-top: 12px;">
                <strong>🚨 Red Flags:</strong><br>
                ${publication.red_flags.map(f => `• ${f}`).join('<br>')}
            </div>
        `;
    } else {
        redContainer.innerHTML = '';
    }

    // Green flags
    if (publication.green_flags && publication.green_flags.length > 0) {
        greenContainer.innerHTML = `
            <div class="success-box" style="margin-top: 12px;">
                <strong>✅ Positive Indicators:</strong><br>
                ${publication.green_flags.map(f => `• ${f}`).join('<br>')}
            </div>
        `;
    } else {
        greenContainer.innerHTML = '';
    }
}

function displayCounterPerspective(counter, analysis) {
    const section = document.getElementById('counter-section');
    const container = document.getElementById('counter-perspective');

    if (!counter) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';

    const counterPub = counter.publication;
    const counterScore = counterPub.credibility_score || 0;
    const counterName = counterPub.name || counterPub.domain;

    let scoreClass = 'low';
    let scoreEmoji = '🔴';
    if (counterScore >= 7) {
        scoreClass = 'high';
        scoreEmoji = '🟢';
    } else if (counterScore >= 5) {
        scoreClass = 'medium';
        scoreEmoji = '🟡';
    }

    let html = `
        <div class="counter-article">
            <div class="credibility-badge credibility-${scoreClass}" style="margin-bottom: 8px;">
                ${scoreEmoji} Counter Source: ${counterScore}/10
            </div>
            <p style="margin: 8px 0;"><strong>${counterName}</strong></p>
            <p style="margin: 8px 0; font-size: 13px;">
                <a href="${counter.article.url}" target="_blank">${counter.article.title}</a>
            </p>
            <p style="margin: 8px 0; font-size: 12px; color: #7f8c8d;">${counter.article.snippet}</p>
    `;

    // Show funding comparison
    if (counterPub.funding_sources && counterPub.funding_sources.length > 0) {
        html += `
            <p style="margin: 8px 0; font-size: 12px;">
                <span class="info-label">💰 Funding:</span> ${counterPub.funding_sources.join(', ')}
            </p>
        `;
    }

    // Show credibility difference
    if (analysis && analysis.credibility_difference) {
        const diff = analysis.credibility_difference;
        html += `
            <p style="margin: 8px 0; font-size: 12px; color: #e74c3c;">
                <strong>Credibility gap: ${diff.toFixed(1)} points</strong>
            </p>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

function displayAnalysisWarning(analysis) {
    const container = document.getElementById('analysis-warning');

    if (!analysis || !analysis.warning) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    container.className = 'section warning';
    container.innerHTML = `
        <strong>⚠️ ${analysis.warning}</strong>
        ${analysis.recommendation ? `<p style="margin: 8px 0 0 0; font-size: 12px;">${analysis.recommendation}</p>` : ''}
    `;
}

function displayMythDetection(myths) {
    const section = document.getElementById('myth-section');
    const container = document.getElementById('myth-detection');

    if (!myths || myths.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';

    let html = '';
    myths.forEach(myth => {
        html += `
            <div class="conflict" style="margin-bottom: 8px;">
                <strong>${myth.claim}</strong><br>
                <span style="font-size: 12px;">${myth.reality}</span>
            </div>
        `;
    });

    container.innerHTML = html;
}

function displayMissingContext(missing) {
    const container = document.getElementById('missing-context');

    if (!missing || missing.length === 0) {
        container.innerHTML = '<p style="font-size: 12px; color: #7f8c8d;">No critical issues identified.</p>';
        return;
    }

    let html = '<ul style="margin: 8px 0; padding-left: 20px;">';
    missing.forEach(item => {
        html += `<li style="margin: 4px 0; font-size: 13px;">${item}</li>`;
    });
    html += '</ul>';

    container.innerHTML = html;
}
