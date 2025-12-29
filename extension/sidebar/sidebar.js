const API_URL = 'http://localhost:5000';

// Generate unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Session storage for duplicate prevention
function isAnalysisInProgress(url) {
    const inProgress = sessionStorage.getItem('aletheia_analyzing');
    const analyzingUrl = sessionStorage.getItem('aletheia_url');
    const timestamp = parseInt(sessionStorage.getItem('aletheia_timestamp') || '0');
    
    const now = Date.now();
    if (inProgress === 'true' && analyzingUrl === url && (now - timestamp) < 10000) {
        return true;
    }
    return false;
}

function setAnalysisInProgress(url, inProgress) {
    sessionStorage.setItem('aletheia_analyzing', inProgress ? 'true' : 'false');
    sessionStorage.setItem('aletheia_url', url);
    sessionStorage.setItem('aletheia_timestamp', Date.now().toString());
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'analyze') {
        if (isAnalysisInProgress(message.url)) {
            console.log('⚠️ Analysis already in progress for this URL, ignoring duplicate request');
            return;
        }
        
        analyzeArticle(message.url, message.title);
    }
});

async function analyzeArticle(url, title) {
    if (isAnalysisInProgress(url)) {
        console.log('⚠️ Duplicate request blocked');
        return;
    }
    
    setAnalysisInProgress(url, true);
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    const sessionId = generateSessionId();
    
    try {
        // Try streaming first
        const response = await fetch(`${API_URL}/analyze-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, title, session_id: sessionId })
        });
        
        if (!response.ok || !response.body) {
            throw new Error('Streaming not supported, using fallback');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.complete) {
                        // Analysis complete
                        displayResults(data.result, title, url);
                    } else if (data.error) {
                        // Error occurred
                        document.getElementById('loading').innerHTML = `
                            <p>⚠️ Error analyzing article.</p>
                            <p>${data.error}</p>
                        `;
                    } else {
                        // Progress update - NEW PART
                        updateLoadingProgress(data.message, data.submessage);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Streaming error, using fallback:', error);
        fallbackAnalyze(url, title);
    } finally {
        setTimeout(() => {
            setAnalysisInProgress(url, false);
        }, 3000);
    }
}

let progressSteps = [];

function updateLoadingProgress(message, submessage) {
    const loadingEl = document.getElementById('loading');
    
    // Add new step
    progressSteps.push({ message, submessage });
    
    // Show all steps
    let html = '<div style="padding: 15px; font-size: 13px; line-height: 1.6;">';
    
    progressSteps.forEach((s, i) => {
        const isLatest = i === progressSteps.length - 1;
        
        // Main message
        html += `<div style="opacity: ${isLatest ? '1' : '0.5'}; margin-bottom: 8px;">`;
        html += `<strong>${s.message}</strong>`;
        
        // Submessage if exists
        if (s.submessage) {
            html += `<div style="margin-left: 15px; color: #666; font-size: 12px;">${s.submessage}</div>`;
        }
        
        html += `</div>`;
    });
    
    html += '</div>';
    loadingEl.innerHTML = html;
}

async function fallbackAnalyze(url, title) {
    // Fallback to original non-streaming API
    try {
        // Reset steps
        progressSteps = [];
        
        document.getElementById('loading').innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <p style="font-size: 18px; margin-bottom: 10px;">🔍 Analyzing article...</p>
                <p style="font-size: 12px; color: #666;">This may take 10-15 seconds</p>
            </div>
        `;
        
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, title })
        });
        
        const data = await response.json();
        displayResults(data, title, url);
        
    } catch (error) {
        console.error('Fallback error:', error);
        document.getElementById('loading').innerHTML = `
            <p style="padding: 20px;">⚠️ Error connecting to Aletheia API.</p>
            <p style="padding: 0 20px;">Make sure the backend is running on port 5000.</p>
        `;
    }
}

// KEEP ALL YOUR EXISTING DISPLAY FUNCTIONS BELOW - DON'T CHANGE ANYTHING
// displayResults, displayClaimClassification, displayCredibilityScore, 
// displayFundingInfo, displayFlags, displayAdaptiveEvidence,
// displayAnalysisWarning, displayMythDetection, displayMissingContext

function displayResults(data, title, url) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
    
    document.getElementById('article-title').textContent = title;
    const domain = new URL(url).hostname;
    document.getElementById('article-source').textContent = domain;
    
    displayClaimClassification(data.claim_classification);
    displayCredibilityScore(data.main_publication);
    displayFundingInfo(data.main_publication);
    displayFlags(data.main_publication);
    displayAdaptiveEvidence(data.evidence, data.analysis);
    displayAnalysisWarning(data.analysis);
    displayMythDetection(data.myths);
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
    
    if (warning) {
        html += `<div style="margin: 8px 0; font-size: 13px;">${warning}</div>`;
    }
    
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
        
        if (isAcademic && hasUnknownFunding) {
            html += `<div class="warning" style="margin-top: 8px; font-size: 12px;">
                ℹ️ <strong>Academic Funding Note:</strong> Universities often receive corporate research grants. 
                Specific funding sources for this department/article may not be publicly disclosed.
            </div>`;
        }
        
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
    
    if (conflicts.length > 0) {
        html += `<div class="conflict" style="margin-top: 12px;">
            <strong>⚠️ Conflicts of Interest:</strong>
            <ul style="margin: 4px 0; padding-left: 20px;">`;
        
        conflicts.forEach(conflict => {
            html += `<li>${conflict}</li>`;
        });
        
        html += `</ul></div>`;
    }
    
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
    
    if (publication.red_flags && publication.red_flags.length > 0) {
        html += `<div class="conflict">
            <strong>🚩 Red Flags:</strong><br>
            ${publication.red_flags.map(f => `• ${f}`).join('<br>')}
        </div>`;
    }
    
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
    
    let sectionEmoji = '🔍';
    if (label.includes('Independent')) {
        sectionEmoji = '🔬';
    }
    
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
        <div style="background: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
            <div style="font-weight: 600; margin-bottom: 8px;">${sectionEmoji} ${label}</div>
            <div class="credibility-badge credibility-${scoreClass}" style="display: inline-block; margin-bottom: 8px;">
                ${scoreEmoji} ${evidenceScore.toFixed(1)}/10
            </div>
            <div style="font-size: 13px; margin-top: 8px;">
                <strong>${evidenceName}</strong><br>
                <a href="${evidence.article.url}" target="_blank" style="color: #3498db; text-decoration: none;">
                    ${evidence.article.title}
                </a>
            </div>
    `;
    
    if (evidencePub.funding_sources && evidencePub.funding_sources.length > 0) {
        html += `<div style="font-size: 12px; color: #666; margin-top: 8px;">
            💰 Funding: ${evidencePub.funding_sources.slice(0, 2).join(', ')}
        </div>`;
    }
    
    // ADD THIS - Show funding diversity
    if (analysis && analysis.funding_diversity !== undefined) {
        const diversity = analysis.funding_diversity;
        let diversityColor = '#27ae60';
        let diversityText = 'High diversity';
        
        if (diversity < 30) {
            diversityColor = '#e74c3c';
            diversityText = 'Low diversity - similar funding';
        } else if (diversity < 60) {
            diversityColor = '#f39c12';
            diversityText = 'Moderate diversity';
        }
        
        html += `<div style="font-size: 12px; margin-top: 8px; padding: 8px; background: ${diversityColor}22; border-left: 3px solid ${diversityColor}; border-radius: 3px;">
            <strong>🔀 Funding Diversity:</strong> ${diversity.toFixed(0)}%
            <div style="color: #666; font-size: 11px; margin-top: 2px;">${diversityText}</div>
        </div>`;
    }
    
    html += `</div>`;
    
    container.innerHTML = html;
}

function displayAnalysisWarning(analysis) {
    const container = document.getElementById('analysis-warning');
    
    if (!analysis || !analysis.warning) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    let warningColor = '#f39c12';
    if (analysis.warning.includes('CRITICAL')) {
        warningColor = '#e74c3c';
    }
    
    container.innerHTML = `
        <div style="background: ${warningColor}22; border-left: 4px solid ${warningColor}; padding: 12px; border-radius: 4px;">
            <div style="font-weight: 600; margin-bottom: 6px;">${analysis.warning}</div>
            ${analysis.recommendation ? `<div style="font-size: 13px;">${analysis.recommendation}</div>` : ''}
        </div>
    `;
}

function displayMythDetection(myths) {
    const section = document.getElementById('myths-section');
    const container = document.getElementById('detected-myths');
    
    if (!myths || myths.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
    let html = '';
    myths.forEach(myth => {
        html += `
            <div class="conflict" style="margin-bottom: 10px;">
                <strong>⚠️ ${myth.myth}</strong><br>
                <div style="font-size: 13px; margin-top: 6px;">
                    <strong>Reality:</strong> ${myth.reality}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayMissingContext(context) {
    const container = document.getElementById('missing-context');
    
    if (!context || context.length === 0) {
        container.innerHTML = '<p style="font-size: 13px; color: #666;">No additional context needed.</p>';
        return;
    }
    
    let html = '<ul style="margin: 0; padding-left: 20px; font-size: 13px;">';
    context.forEach(item => {
        html += `<li style="margin: 6px 0;">${item}</li>`;
    });
    html += '</ul>';
    
    container.innerHTML = html;
}
