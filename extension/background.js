// Open sidebar when extension icon is clicked
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ windowId: tab.windowId });
  
  // Send message to sidebar with current tab info
  chrome.runtime.sendMessage({
    action: 'analyze',
    url: tab.url,
    title: tab.title
  });
});
