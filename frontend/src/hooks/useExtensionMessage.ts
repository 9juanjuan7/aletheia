import { useEffect, useState } from "react";

export interface ExtensionMessage {
  action: string;
  url: string;
  title: string;
}

/**
 * Hook to listen for messages from extension background.js
 * Handles extension message API with fallback for development
 */
export function useExtensionMessage() {
  const [message, setMessage] = useState<ExtensionMessage | null>(null);

  useEffect(() => {
    // Check if running in extension context
    if (typeof chrome !== "undefined" && chrome.runtime) {
      const handleMessage = (
        incomingMessage: any,
        sender: chrome.runtime.MessageSender,
        sendResponse: (response?: any) => void
      ) => {
        if (incomingMessage.action === "analyze") {
          setMessage({
            action: incomingMessage.action,
            url: incomingMessage.url,
            title: incomingMessage.title,
          });
        }
        sendResponse({ received: true });
      };

      chrome.runtime.onMessage.addListener(handleMessage);

      return () => {
        chrome.runtime.onMessage.removeListener(handleMessage);
      };
    }
  }, []);

  return message;
}
