import { useState, useEffect } from "react";
import { AletheiaSidebar } from "@/components/aletheia/AletheiaSidebar";
import { useExtensionMessage } from "@/hooks/useExtensionMessage";
import { streamAnalysis } from "@/services/api";

// Loading steps
const defaultLoadingSteps = [
  { message: "Extracting article content", submessage: "Parsing HTML and metadata" },
  { message: "Identifying publication", submessage: "Checking credibility database" },
  { message: "Analyzing funding sources", submessage: "Following the money trail" },
  { message: "Finding counter-perspectives", submessage: "Searching independent sources" },
  { message: "Detecting health myths", submessage: "Cross-referencing claims" },
  { message: "Generating analysis report", submessage: "Compiling findings" }
];

const Index = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<any | undefined>(undefined);
  const [steps, setSteps] = useState<AnalysisProgress[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [articleTitle, setArticleTitle] = useState<string>("Waiting for article...");
  const [articleUrl, setArticleUrl] = useState<string>("");

  // Listen for messages from extension background.js
  const extensionMessage = useExtensionMessage();

  // Perform analysis when message received
  useEffect(() => {
    if (extensionMessage?.url && extensionMessage?.title) {
      analyzeArticle(extensionMessage.url, extensionMessage.title);
    }
  }, [extensionMessage]);

  const analyzeArticle = async (url: string, title: string) => {
    setIsLoading(true);
    setError(null);
    setData(undefined);
    setArticleTitle(title);
    setArticleUrl(url);

    // Show default loading steps (without emojis)
    setSteps(defaultLoadingSteps);
    setCurrentStep(0);

    // Simulate step progression
    let step = 0;
    const stepInterval = setInterval(() => {
      if (step < defaultLoadingSteps.length - 1) {
        step++;
        setCurrentStep(step);
      } else {
        clearInterval(stepInterval);
      }
    }, 1500);

    try {
      const sessionId = `session_${Date.now()}`;
      
      const result = await streamAnalysis(
        url,
        title,
        sessionId,
        () => {
          // Just consume progress, don't display it
        }
      );

      clearInterval(stepInterval);
      setData(result);
      setIsLoading(false);
    } catch (err) {
      clearInterval(stepInterval);
      const errorMsg = err instanceof Error ? err.message : "Failed to analyze article";
      setError(errorMsg);
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    if (articleUrl && articleTitle) {
      analyzeArticle(articleUrl, articleTitle);
    }
  };

  return (
    <div className="min-h-screen bg-muted flex items-start justify-center py-8">
      <div className="shadow-elevated">
        {error ? (
          <div className="p-8 bg-red-50 border border-red-200 rounded-lg max-w-md">
            <h3 className="text-red-800 font-semibold mb-2">Analysis Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
            <p className="text-red-600 text-xs mt-4">
              Make sure the Flask backend is running at http://localhost:5000
            </p>
          </div>
        ) : (
          <AletheiaSidebar
            isLoading={isLoading}
            loadingSteps={steps}
            currentLoadingStep={currentStep}
            articleTitle={articleTitle}
            articleUrl={articleUrl}
            data={data}
            onRefresh={handleRefresh}
          />
        )}
      </div>
    </div>
  );
};

export default Index;
