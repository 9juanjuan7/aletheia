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
    document.getElementById('loading').innerHTML = 
      '<p class="warning">⚠️ Error connecting to Aletheia API. Make sure the backend is running.</p>';
  }
}

function displayResults(data, title, url) {
  document.getElementById('loading').style.display = 'none';
  document.getElementById('results').style.display = 'block';

  // Article info
  document.getElementById('article-title').textContent = title;
  const domain = new URL(url).hostname;
  document.getElementById('article-source').textContent = domain;

  // Funding info
  displayFundingInfo(data.publication);

  // Myth detection
  displayMythDetection(data.myths);

  // Comparative coverage
  displayComparativeCoverage(data.related_articles);

  // Missing context
  displayMissingContext(data.missing_context);
}

function displayFundingInfo(publication) {
  const container = document.getElementById('funding-info');
  
  if (!publication) {
    container.innerHTML = '<p>ℹ️ Publication not in our database yet.</p>';
    return;
  }

  let html = `
    <div class="info-item">
      <span class="info-label">Owner:</span> ${publication.owner}
    </div>
    <div class="info-item">
      <span class="info-label">Funding:</span> ${publication.funding_model}
    </div>
  `;

  if (publication.major_advertisers && publication.major_advertisers.length > 0) {
    html += `
      <div class="info-item">
        <span class="info-label">Major Advertisers:</span>
        <ul>
          ${publication.major_advertisers.map(adv => `<li>${adv}</li>`).join('')}
        </ul>
      </div>
    `;
  }

  if (publication.conflicts && publication.conflicts.length > 0) {
    html += `<div class="conflict">⚠️ Potential conflicts of interest detected:</div>`;
    publication.conflicts.forEach(conflict => {
      html += `<div class="warning">${conflict}</div>`;
    });
  }

  container.innerHTML = html;
}

function displayMythDetection(myths) {
  const container = document.getElementById('myth-detection');
  
  if (!myths || myths.length === 0) {
    container.innerHTML = '<p>✅ No known nutrition myths detected.</p>';
    return;
  }

  let html = '<div class="conflict">⚠️ This article may repeat known misinformation:</div>';
  
  myths.forEach(myth => {
    html += `
      <div class="warning">
        <strong>Claim:</strong> "${myth.claim}"<br>
        <strong>Origin:</strong> ${myth.origin}<br>
        <strong>Who benefits:</strong> ${myth.who_benefits}<br>
        <strong>Current science:</strong> ${myth.current_science}
      </div>
    `;
  });

  container.innerHTML = html;
}

function displayComparativeCoverage(articles) {
  const container = document.getElementById('comparative-coverage');
  
  if (!articles || articles.length === 0) {
    container.innerHTML = '<p>ℹ️ No related coverage found.</p>';
    return;
  }

  let html = `<p>${articles.length} other sources covered similar topics:</p>`;
  
  articles.forEach(article => {
    html += `
      <div class="related-article">
        <a href="${article.url}" target="_blank">${article.title}</a>
        <span class="badge badge-different">Different perspective</span>
        <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px;">
          ${article.source}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function displayMissingContext(missing) {
  const container = document.getElementById('missing-context');
  
  if (!missing || missing.length === 0) {
    container.innerHTML = '<p>ℹ️ Analysis in progress...</p>';
    return;
  }

  let html = '<p>This article may not mention:</p><ul>';
  missing.forEach(item => {
    html += `<li>✗ ${item}</li>`;
  });
  html += '</ul>';

  container.innerHTML = html;
}
