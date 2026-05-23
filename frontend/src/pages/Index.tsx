import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Link as LinkIcon, Sparkles, ArrowRight, Plus, Mic2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import LinkCard from "@/components/LinkCard";
import { extractBatch, batchResponseToExtractedContent, ExtractedContent } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface LinkItem {
  id: string;
  url: string;
  type: "article" | "pdf" | "video" | "link";
}

const detectLinkType = (url: string): LinkItem["type"] => {
  if (url.includes("youtube.com") || url.includes("vimeo.com") || url.includes("youtu.be")) {
    return "video";
  }
  if (url.endsWith(".pdf")) {
    return "pdf";
  }
  if (
    url.includes("medium.com") ||
    url.includes("substack.com") ||
    url.includes("blog") ||
    url.includes("article")
  ) {
    return "article";
  }
  return "link";
};

const Index = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [inputValue, setInputValue] = useState("");
  const [links, setLinks] = useState<LinkItem[]>([]);
  const [extraContent, setExtraContent] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0 });

  const addLink = () => {
    if (!inputValue.trim()) return;

    const url = inputValue.trim();
    const linkType = detectLinkType(url);

    // Prevent YouTube videos and PDFs
    if (linkType === "video") {
      toast({
        title: "Video links not supported",
        description: "YouTube and video links are not supported. Please add article links only.",
        variant: "destructive",
      });
      return;
    }

    if (linkType === "pdf") {
      toast({
        title: "PDF files not supported",
        description: "PDF files are not supported. Please add article links only.",
        variant: "destructive",
      });
      return;
    }

    const newLink: LinkItem = {
      id: Date.now().toString(),
      url: url,
      type: linkType,
    };

    setLinks((prev) => [...prev, newLink]);
    setInputValue("");
  };

  const removeLink = (id: string) => {
    setLinks((prev) => prev.filter((link) => link.id !== id));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      addLink();
    }
  };

  const handleGenerate = async () => {
    if (links.length === 0) return;
    
    setIsGenerating(true);
    setGenerationProgress({ current: 0, total: links.length });
    
    try {
      const urls = links.map(link => link.url);
      console.log("[Index] Starting batch extraction with URLs:", urls);
      
      // Use batch endpoint to get combined dictionary format
      const batchResponse = await extractBatch(urls, extraContent.trim() || undefined);
      console.log("[Index] Batch response received:", batchResponse);
      
      // Convert batch response to ExtractedContent array format
      const extractedContents: ExtractedContent[] = batchResponseToExtractedContent(
        batchResponse,
        urls
      );
      
      console.log("[Index] Converted to ExtractedContent:", extractedContents);
      
      // Update progress
      setGenerationProgress({ current: links.length, total: links.length });
      
      toast({
        title: "Content Extracted",
        description: `Successfully extracted content from ${links.length} link(s)`,
      });
      
      // Navigate to player with both links and extracted content
      navigate("/player", { 
        state: { 
          links,
          extractedContents,
          batchResponse, // Also pass the raw batch response
          extraContent: extraContent.trim() || undefined // Pass extra content if provided
        } 
      });
    } catch (error) {
      console.error("[Index] Error generating podcast:", error);
      toast({
        title: "Generation Failed",
        description: error instanceof Error 
          ? error.message 
          : "Failed to extract content from URLs. Please try again.",
        variant: "destructive",
      });
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-to-bl from-primary/10 via-transparent to-transparent blur-3xl" />
        <div className="absolute -bottom-1/2 -left-1/2 w-full h-full bg-gradient-to-tr from-secondary/10 via-transparent to-transparent blur-3xl" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12 max-w-3xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-secondary mb-6 glow-effect"
          >
            <Mic2 className="w-8 h-8 text-primary-foreground" />
          </motion.div>
          
          <h1 className="text-4xl md:text-5xl font-bold font-display mb-4">
            <span className="gradient-text">Podify</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-md mx-auto">
            Transform articles into engaging podcasts with AI
          </p>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
          ⚠️ Note: Audio generation is currently disabled due to API limitations. However, generation and summary is available. A demo video is available on my website.
          </p>
        </motion.div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-8"
        >
          <div className="glass-card rounded-2xl p-6">
            <label className="block text-sm font-medium text-muted-foreground mb-3">
              Add your content links
            </label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Paste article URL..."
                  className="w-full h-12 pl-12 pr-4 bg-muted/50 border border-border rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                />
              </div>
              <Button
                onClick={addLink}
                variant="gradient"
                size="icon"
                className="h-12 w-12 rounded-xl"
              >
                <Plus className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Links List */}
        <AnimatePresence mode="popLayout">
          {links.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3 mb-8"
            >
              {links.map((link, index) => (
                <LinkCard
                  key={link.id}
                  url={link.url}
                  type={link.type}
                  onRemove={() => removeLink(link.id)}
                  index={index}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Extra Content Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mb-8"
        >
          <div className="glass-card rounded-2xl p-6">
            <label className="block text-sm font-medium text-muted-foreground mb-3">
              User Extra Content <span className="text-xs text-muted-foreground/70">(optional)</span>
            </label>
            <Textarea
              value={extraContent}
              onChange={(e) => setExtraContent(e.target.value)}
              placeholder="Add any additional content, notes, or context you'd like included in the podcast..."
              className="min-h-[100px] bg-muted/50 border-border resize-none"
            />
          </div>
        </motion.div>

        {/* Generate Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex flex-col items-center gap-4"
        >
          <Button
            onClick={handleGenerate}
            disabled={links.length === 0 || isGenerating}
            variant="gradient"
            size="xl"
            className="group"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2 group-hover:rotate-12 transition-transform" />
                Generate Podcast
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </Button>
          
          {isGenerating && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm text-muted-foreground"
            >
              Extracting content from {generationProgress.current} of {generationProgress.total} links...
            </motion.div>
          )}
        </motion.div>

        {/* Info */}
        {links.length === 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-center text-sm text-muted-foreground mt-8"
          >
            Add at least one link to generate your podcast
          </motion.p>
        )}
      </div>
    </div>
  );
};

export default Index;
