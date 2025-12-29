const API_URL = 'http://localhost:5000';

// Analysis lock to prevent duplicate requests
let analysisInProgress = false;
let currentAnalysisUrl = null;

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'analyze') {
        // Prevent duplicate analysis
        if (analysisInProgress && currentAnalysisUrl === message.url) {
            console.log('Analysis already in progress for this URL');
            return;
        }
        
        analyzeArticle(message.url, message.title);
    }
});

async function analyzeArticle(url, title) {
    // Set lock
    if (analysisInProgress && currentAnalysisUrl === url) {
        console.log('Analysis already in progress, ignoring duplicate request');
        return;
    }
    
    analysisInProgress = true;
    currentAnalysisUrl = url;
    
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
            <p>Make sure the backend is running on port 5000.</p>
        `;
    } finally {
        // Release lock after 2 seconds
        setTimeout(() => {
            analysisInProgress = false;
            currentAnalysisUrl = null;
        }, 2000);
    }
}
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
            <p>Make sure the backend is running on port 5000.</p>
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
    
    // IMPORTANT: Display claim classification first (new section)
    displayClaimClassification(data.claim_classification);
    
    // Main source credibility
    displayCredibilityScore(data.main_publication);
    displayFundingInfo(data.main_publication);
    displayFlags(data.main_publication);
    
    // Adaptive evidence (replaces counter-perspective)
    displayAdaptiveEvidence(data.evidence, data.analysis);
    
    // Analysis warning
    displayAnalysisWarning(data.analysis);
    
    // Myth detection
    displayMythDetection(data.myths);
    
    // Missing context
    displayMissingContext(data.missing_context);
}

function displayClaimClassification(classification) {
    const section = document.getElementById('classification-section');
    const container = document.getElementById('claim-classification');
    
    if (!classification) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
    const classType = classification.classification || 'UNKNOWN';
    const warning = classification.warning;
    const redFlags = classification.red_flags || [];
    
    // Determine styling based on classification
    let classEmoji = 'ℹ️';
    let classColor = '#3498db';
    let classText = classType.replace(/_/g, ' ');
    
    if (classType.includes('MANUFACTURED_CONSENSUS') || classType.includes('INDUSTRY_NARRATIVE')) {
        classEmoji = '🚨';
        classColor = '#e74c3c';
    } else if (classType.includes('ESTABLISHED_FACT_VERIFIED')) {
        classEmoji = '✅';
        classColor = '#27ae60';
    } else if (classType === 'FRINGE' || classType === 'COMMERCIAL_CLAIM') {
        classEmoji = '⚠️';
        classColor = '#f39c12';
    } else if (classType.includes('CONTESTED')) {
        classEmoji = '⚖️';
        classColor = '#f39c12';
    }
    
    let html = `
        <div style="border-left: 4px solid ${classColor}; padding: 12px; background: #f8f9fa; border-radius: 4px;">
            <div style="font-weight: 600; margin-bottom: 8px;">
                ${classEmoji} <span style="color: ${classColor};">${classText}</span>
            </div>
    `;
    
    // Add warning if exists
    if (warning) {
        html += `<div style="margin: 8px 0; font-size: 13px;">${warning}</div>`;
    }
    
    // Add red flags
    if (redFlags.length > 0) {
        html += `<div style="margin-top: 8px; font-size: 12px; color: #666;">`;
        redFlags.slice(0, 3).forEach(flag => {
            html += `<div style="margin: 4px 0;">• ${flag}</div>`;
        });
        html += `</div>`;
    }
    
    html += `</div>`;
    
    container.innerHTML = html;
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
            ${scoreEmoji} ${score.toFixed(1)}/10
        </div>
        ${publication.credibility_explanation ? 
            `<p style="margin-top: 12px; font-size: 13px;">
                <strong>${name}</strong><br>
                ${publication.credibility_explanation}
            </p>` : ''}
    `;
}

function displayFundingInfo(publication) {
    const container = document.getElementById('funding-info');
    if (!publication) return;
    
    let html = '<div>';
    
    const ownership = publication.ownership || '';
    const fundingSources = publication.funding_sources || [];
    const conflicts = publication.conflicts_of_interest || [];
    const industryTies = publication.industry_ties || [];
    const transparency = publication.funding_transparency || 'unknown';
    
    // Detect source type
    const isAcademic = ownership.toLowerCase().includes('university') || 
                      ownership.toLowerCase().includes('college') ||
                      publication.domain.includes('.edu');
    
    const isGovernment = ownership.toLowerCase().includes('department of') ||
                        ownership.toLowerCase().includes('agency') ||
                        ownership.toLowerCase().includes('cdc') ||
                        ownership.toLowerCase().includes('fda') ||
                        ownership.toLowerCase().includes('nih') ||
                        ownership.toLowerCase().includes('usda') ||
                        publication.domain.includes('.gov');
    
    // Ownership with indicator
    if (ownership && ownership !== 'Unknown') {
        let ownershipBadge = '';
        if (isGovernment) {
            ownershipBadge = '<span style="font-size: 11px; color: #e74c3c; font-style: italic;"> (Government Agency - Check for Industry Capture)</span>';
        } else if (isAcademic) {
            ownershipBadge = '<span style="font-size: 11px; color: #7f8c8d; font-style: italic;"> (Academic Institution)</span>';
        }
        
        html += `<div class="info-item">
            <span class="info-label">🏢 Ownership:</span> 
            ${ownership}${ownershipBadge}
        </div>`;
    }
    
    // Funding sources with context
    if (fundingSources.length > 0) {
        const fundingStr = fundingSources.join(', ').toLowerCase();
        const hasUnknownFunding = fundingStr.includes('unclear') || 
                                 fundingStr.includes('not disclosed') ||
                                 fundingStr.includes('not available');
        const hasGovernmentFunding = fundingStr.includes('government') || 
                                    fundingStr.includes('federal') ||
                                    fundingStr.includes('usda') ||
                                    fundingStr.includes('fda') ||
                                    fundingStr.includes('nih');
        
        html += `<div class="info-item">
            <span class="info-label">💰 Funding Sources:</span><br>
            <ul style="margin: 4px 0; padding-left: 20px; font-size: 13px;">`;
        
        fundingSources.forEach(source => {
            html += `<li>${source}</li>`;
        });
        
        html += `</ul></div>`;
        
        // Academic funding context
        if (isAcademic && hasUnknownFunding) {
            html += `<div class="warning" style="margin-top: 8px; font-size: 12px;">
                ℹ️ <strong>Academic Funding Note:</strong> Universities often receive corporate research grants. 
                Specific funding sources for this department/article may not be publicly disclosed.
            </div>`;
        }
        
        // Government funding context
        if (isGovernment || hasGovernmentFunding) {
            html += `<div class="warning" style="margin-top: 8px; font-size: 12px;">
                ⚠️ <strong>Government Funding Note:</strong> Government agencies can be influenced by industry lobbying, 
                revolving door employment, and regulatory capture. Check for specific industry ties.
            </div>`;
        }
        
    } else if (isAcademic) {
        html += `<div class="info-item">
            <span class="info-label">💰 Funding Sources:</span> 
            <span style="color: #e74c3c;">Not disclosed</span>
        </div>`;
        html += `<div class="warning" style="margin-top: 8px; font-size: 12px;">
            ℹ️ <strong>Academic Funding Note:</strong> Universities often receive corporate research grants, 
            but this institution does not publicly disclose funding sources. Cannot verify independence.
        </div>`;
    } else if (isGovernment) {
        html += `<div class="info-item">
            <span class="info-label">💰 Funding Sources:</span> 
            Federal government appropriations
        </div>`;
        html += `<div class="warning" style="margin-top: 8px; font-size: 12px;">
            ⚠️ <strong>Government Agency Note:</strong> Check for industry lobbying influence, 
            revolving door employment, and regulatory capture. Government authority ≠ independence.
        </div>`;
    }
    
    // Funding transparency indicator
    if (transparency && transparency !== 'unknown') {
        let transparencyColor = '#27ae60';
        let transparencyText = 'High';
        
        if (transparency === 'low') {
            transparencyColor = '#e74c3c';
            transparencyText = 'Low';
        } else if (transparency === 'medium') {
            transparencyColor = '#f39c12';
            transparencyText = 'Medium';
        } else if (transparency === 'none') {
            transparencyColor = '#c0392b';
            transparencyText = 'None';
        }
        
        html += `<div class="info-item" style="margin-top: 8px;">
            <span class="info-label">🔍 Funding Transparency:</span> 
            <span style="color: ${transparencyColor}; font-weight: 600;">${transparencyText}</span>
        </div>`;
    }
    
    // Conflicts of interest (prominent display)
    if (conflicts.length > 0) {
        html += `<div class="conflict" style="margin-top: 12px;">
            <strong>⚠️ Conflicts of Interest:</strong>
            <ul style="margin: 4px 0; padding-left: 20px;">`;
        
        conflicts.forEach(conflict => {
            html += `<li>${conflict}</li>`;
        });
        
        html += `</ul></div>`;
    }
    
    // Industry ties
    if (industryTies.length > 0) {
        html += `<div class="info-item" style="margin-top: 8px;">
            <span class="info-label">🔗 Industry Ties:</span><br>
            <span style="font-size: 13px;">${industryTies.join(', ')}</span>
        </div>`;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function displayFlags(publication) {
    const container = document.getElementById('flags');
    if (!publication) return;
    
    let html = '';
    
    // Red flags
    if (publication.red_flags && publication.red_flags.length > 0) {
        html += `<div class="conflict">
            <strong>🚩 Red Flags:</strong><br>
            ${publication.red_flags.map(f => `• ${f}`).join('<br>')}
        </div>`;
    }
    
    // Green flags
    if (publication.green_flags && publication.green_flags.length > 0) {
        html += `<div class="success-box">
            <strong>✅ Green Flags:</strong><br>
            ${publication.green_flags.map(f => `• ${f}`).join('<br>')}
        </div>`;
    }
    
    container.innerHTML = html;
}

function displayAdaptiveEvidence(evidence, analysis) {
    const section = document.getElementById('evidence-section');
    const container = document.getElementById('adaptive-evidence');
    
    if (!evidence || !evidence.publication) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
    const evidencePub = evidence.publication;
    const evidenceScore = evidencePub.credibility_score || 0;
    const evidenceName = evidencePub.name || evidencePub.domain;
    const label = evidence.label || 'Additional Evidence';
    
    // Determine section title emoji based on label
    let sectionEmoji = '🔍';
    if (label.includes('Independent')) {
        sectionEmoji = '🔬';
    } else if (label.includes('Confirmation')) {
        sectionEmoji = '✅';
    } else if (label.includes('Debunk') || label.includes('Evidence-Based')) {
        sectionEmoji = '🛡️';
    }
    
    // Update section title dynamically
    document.querySelector('#evidence-section h2').innerHTML = `${sectionEmoji} ${label}`;
    
    let scoreClass = 'low';
    let scoreEmoji = '🔴';
    if (evidenceScore >= 7) {
        scoreClass = 'high';
        scoreEmoji = '🟢';
    } else if (evidenceScore >= 5) {
        scoreClass = 'medium';
        scoreEmoji = '🟡';
    }
    
    let html = `
        <div class="counter-article">
            <div style="margin-bottom: 8px;">
                <div class="credibility-badge credibility-${scoreClass}" style="font-size: 14px; padding: 4px 12px;">
                    ${scoreEmoji} ${evidenceScore.toFixed(1)}/10
                </div>
            </div>
            <a href="${evidence.article.url}" target="_blank">
                <strong>${evidence.article.title}</strong>
            </a>
            <p style="margin: 8px 0; font-size: 13px; color: #555;">
                ${evidence.article.snippet}
            </p>
            <div class="info-item" style="margin-top: 8px;">
                <span class="info-label">📰 Source:</span> 
                <strong>${evidenceName}</strong>
            </div>
    `;
    
    // Show funding comparison if available
    if (evidencePub.funding_sources && evidencePub.funding_sources.length > 0) {
        html += `
            <div class="info-item">
                <span class="info-label">💰 Funding:</span> 
                ${evidencePub.funding_sources.join(', ')}
            </div>
        `;
    }
    
    // Show funding diversity if calculated
    if (analysis && analysis.funding_diversity !== undefined) {
        const diversity = analysis.funding_diversity;
        let diversityColor = diversity >= 70 ? '#27ae60' : diversity >= 40 ? '#f39c12' : '#e74c3c';
        html += `
            <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 12px;">
                <span class="info-label">🔄 Funding Diversity:</span> 
                <span style="color: ${diversityColor}; font-weight: 600;">${diversity.toFixed(0)}%</span>
                ${diversity >= 70 ? ' (Different funding sources)' : diversity >= 40 ? ' (Some overlap)' : ' (Similar funding)'}
            </div>
        `;
    }
    
    // Show credibility gap
    if (analysis && analysis.credibility_difference) {
        const diff = analysis.credibility_difference;
        if (diff >= 2) {
            html += `
                <div class="warning" style="margin-top: 12px; font-size: 13px;">
                    <strong>📊 Credibility Gap: ${diff.toFixed(1)} points</strong><br>
                    ${analysis.recommendation || 'Compare both sources carefully'}
                </div>
            `;
        }
    }
    
    html += `</div>`;
    
    container.innerHTML = html;
}

function displayAnalysisWarning(analysis) {
    const container = document.getElementById('analysis-warning');
    
    if (!analysis) {
        container.innerHTML = '';
        return;
    }
    
    // Use classification warning first, fallback to analysis warning
    const warning = analysis.classification_warning || analysis.warning;
    
    if (!warning) {
        container.innerHTML = '';
        return;
    }
    
    // Determine warning style based on content
    let warningClass = 'warning';
    if (warning.includes('🚨') || warning.includes('CRITICAL')) {
        warningClass = 'conflict';
    } else if (warning.includes('✅') || warning.includes('confirmed')) {
        warningClass = 'success-box';
    }
    
    container.innerHTML = `
        <div class="${warningClass}">
            ${warning}
            ${analysis.recommendation ? `<br><br><strong>💡 Recommendation:</strong> ${analysis.recommendation}` : ''}
        </div>
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
            <div class="conflict" style="margin: 8px 0;">
                <strong>${myth.myth}</strong><br>
                <span style="font-size: 12px;">${myth.reality}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayMissingContext(context) {
    const container = document.getElementById('missing-context');
    
    if (!context || context.length === 0) {
        container.innerHTML = '<p style="color: #27ae60;">✅ No critical issues identified.</p>';
        return;
    }
    
    let html = '<ul>';
    context.forEach(item => {
        html += `<li>${item}</li>`;
    });
    html += '</ul>';
    
    container.innerHTML = html;
}
