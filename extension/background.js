// Track domains we've already sent to avoid spamming the local API
const processedDomains = new Set();

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    try {
      const url = new URL(tab.url);
      
      // Ignore chrome:// and local URLs
      if (url.protocol === 'chrome:' || url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
        return;
      }
      
      const domainName = url.hostname.replace("www.", "");
      
      if (!processedDomains.has(domainName)) {
        processedDomains.add(domainName);
        
        // Send to our backend
        fetch('http://localhost:8000/api/v1/domains/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            domain_name: domainName,
            source: "browser_extension" 
          })
        })
        .then(response => response.json())
        .then(data => console.log('Domain tracked:', data))
        .catch(error => console.error('Error tracking domain:', error));
      }
    } catch (e) {
      console.error('Invalid URL:', e);
    }
  }
});
