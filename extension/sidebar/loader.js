// Load Aletheia React app from dist folder
window.__ALETHEIA_EXTENSION__ = true;

async function loadApp() {
  try {
    // Fetch the dist index.html to get asset paths
    const indexPath = chrome.runtime.getURL('../dist/index.html');
    const response = await fetch(indexPath);
    const html = await response.text();
    
    // Parse to find asset references
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    // Load CSS
    const cssLinks = doc.querySelectorAll('link[rel="stylesheet"]');
    cssLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href) {
        const cssPath = href.startsWith('/') ? href.slice(1) : href;
        const newLink = document.createElement('link');
        newLink.rel = 'stylesheet';
        newLink.href = chrome.runtime.getURL(`../dist/${cssPath}`);
        document.head.appendChild(newLink);
      }
    });
    
    // Load JS module
    const scripts = doc.querySelectorAll('script[type="module"]');
    scripts.forEach(script => {
      const src = script.getAttribute('src');
      if (src) {
        const jsPath = src.startsWith('/') ? src.slice(1) : src;
        const moduleUrl = chrome.runtime.getURL(`../dist/${jsPath}`);
        import(moduleUrl).catch(err => {
          console.error('Failed to load module:', err);
        });
      }
    });
  } catch (err) {
    console.error('Failed to load Aletheia app:', err);
    document.body.innerHTML = `
      <div style="color: red; padding: 20px; font-family: monospace;">
        <p><strong>Error loading Aletheia</strong></p>
        <p>${err.message}</p>
        <p style="font-size: 12px;">Make sure you ran: npm run build</p>
      </div>
    `;
  }
}

document.addEventListener('DOMContentLoaded', loadApp);
