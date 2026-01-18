import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX,
  ArrowLeft,
  Share2,
  Download,
  Loader2,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import AudioWaveform from "@/components/AudioWaveform";
import ProgressBar from "@/components/ProgressBar";
import SpeedControl from "@/components/SpeedControl";
import { ExtractedContent, textToSpeech, generateSummary } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface LinkItem {
  id: string;
  url: string;
  type: "article" | "pdf" | "video" | "link";
}

const Player = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [volume, setVolume] = useState(80);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);

  const links: LinkItem[] = location.state?.links || [];
  const extractedContents: ExtractedContent[] = location.state?.extractedContents || [];
  const batchResponse = location.state?.batchResponse;
  const script = batchResponse?.script || location.state?.script;

  // Get summary from batchResponse if available
  useEffect(() => {
    if (batchResponse?.summary) {
      setSummary(batchResponse.summary);
    }
  }, [batchResponse]);

  // Generate summary if not available when sheet opens
  const handleSummaryOpen = async (open: boolean) => {
    setIsSummaryOpen(open);
    
    if (open && !summary && script) {
      setIsLoadingSummary(true);
      try {
        console.log("[Player] Generating summary from script...");
        // Extract URLs from links array
        const userLinks = links.map(link => link.url);
        const generatedSummary = await generateSummary(script, userLinks);
        setSummary(generatedSummary);
        setIsLoadingSummary(false);
      } catch (error) {
        console.error("[Player] Error generating summary:", error);
        setIsLoadingSummary(false);
        toast({
          title: "Summary Generation Failed",
          description: error instanceof Error ? error.message : "Failed to generate summary. Please try again.",
          variant: "destructive",
        });
      }
    }
  };

  // Generate TTS audio when script is available
  useEffect(() => {
    const generateAudio = async () => {
      if (!script || !script.trim()) {
        setIsLoading(false);
        toast({
          title: "No Script Available",
          description: "No podcast script found. Please generate a script first.",
          variant: "destructive",
        });
        return;
      }

      setIsGeneratingAudio(true);
      try {
        console.log("[Player] Generating TTS audio from script...");
        const result = await textToSpeech(script);
        console.log("[Player] TTS audio generated:", result.audio_url);
        setAudioUrl(result.audio_url);
        setIsGeneratingAudio(false);
        setIsLoading(false);
        
        toast({
          title: "Audio Generated",
          description: "Your podcast audio is ready to play!",
        });
      } catch (error) {
        console.error("[Player] Error generating audio:", error);
        setIsGeneratingAudio(false);
        setIsLoading(false);
        toast({
          title: "Audio Generation Failed",
          description: error instanceof Error ? error.message : "Failed to generate audio. Please try again.",
          variant: "destructive",
        });
      }
    };

    generateAudio();
  }, [script, toast]);

  // Update audio element when URL changes
  useEffect(() => {
    if (audioRef.current && audioUrl) {
      audioRef.current.load();
    }
  }, [audioUrl]);

  // Update progress from audio element
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateProgress = () => {
      if (audio.duration) {
        const percent = (audio.currentTime / audio.duration) * 100;
        setProgress(percent);
        setDuration(audio.duration);
      }
    };

    const handleTimeUpdate = () => updateProgress();
    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      updateProgress();
    };
    const handleEnded = () => {
      setIsPlaying(false);
      setProgress(100);
    };

    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [audioUrl]);

  // Sync play/pause with audio element
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.play().catch((error) => {
        console.error("[Player] Error playing audio:", error);
        setIsPlaying(false);
      });
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  // Sync speed with audio element
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.playbackRate = speed;
    }
  }, [speed]);

  // Sync volume with audio element
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.volume = isMuted ? 0 : volume / 100;
    }
  }, [volume, isMuted]);

  const togglePlay = () => {
    if (!audioUrl) return;
    setIsPlaying(!isPlaying);
  };

  const skipForward = () => {
    const audio = audioRef.current;
    if (audio && duration) {
      audio.currentTime = Math.min(duration, audio.currentTime + 10);
    }
  };

  const skipBackward = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = Math.max(0, audio.currentTime - 10);
    }
  };

  const goToStart = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = 0;
      setIsPlaying(false);
    }
  };

  const goToEnd = () => {
    const audio = audioRef.current;
    if (audio && duration) {
      audio.currentTime = duration;
      setIsPlaying(false);
    }
  };

  const toggleMute = () => setIsMuted(!isMuted);

  const handleSeek = (newProgress: number) => {
    const audio = audioRef.current;
    if (audio && duration) {
      audio.currentTime = (newProgress / 100) * duration;
      setProgress(newProgress);
    }
  };

  const formatTime = (seconds: number): string => {
    if (!isFinite(seconds) || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleDownload = async () => {
    if (!audioUrl) {
      toast({
        title: "No Audio Available",
        description: "Audio file is not ready for download yet.",
        variant: "destructive",
      });
      return;
    }

    try {
      // Fetch the audio file
      const response = await fetch(audioUrl);
      if (!response.ok) {
        throw new Error("Failed to fetch audio file");
      }

      // Convert to blob
      const blob = await response.blob();

      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      
      // Generate a meaningful filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
      link.download = `podcast-${timestamp}.mp3`;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Download Started",
        description: "Your podcast audio is being downloaded.",
      });
    } catch (error) {
      console.error("[Player] Error downloading audio:", error);
      toast({
        title: "Download Failed",
        description: error instanceof Error ? error.message : "Failed to download audio. Please try again.",
        variant: "destructive",
      });
    }
  };

  if (isLoading || isGeneratingAudio) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 mx-auto mb-6 rounded-full border-4 border-muted border-t-primary"
          />
          <h2 className="text-xl font-display font-semibold gradient-text mb-2">
            {isGeneratingAudio ? "Generating Audio" : "Loading..."}
          </h2>
          <p className="text-muted-foreground">
            {isGeneratingAudio 
              ? "Converting your script to speech with ElevenLabs..." 
              : "Preparing your podcast..."}
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: isPlaying ? [1, 1.1, 1] : 1,
            opacity: isPlaying ? [0.1, 0.15, 0.1] : 0.1,
          }}
          transition={{ duration: 3, repeat: Infinity }}
          className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-gradient-to-br from-primary/20 to-secondary/20 rounded-full blur-3xl"
        />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 max-w-2xl min-h-screen flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/")}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div className="flex gap-2">
            <Sheet open={isSummaryOpen} onOpenChange={handleSummaryOpen}>
              <SheetTrigger asChild>
                <Button 
                  variant="outline" 
                  size="default" 
                  title="View Summary"
                  className="gap-2 border-primary/50 hover:border-primary hover:bg-primary/10"
                >
                  <FileText className="w-5 h-5" />
                  <span className="hidden sm:inline">Summary</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-full sm:w-[90vw] sm:max-w-4xl overflow-y-auto">
                <SheetHeader>
                  <SheetTitle>Podcast Summary</SheetTitle>
                  <SheetDescription>
                    Key takeaways and detailed notes from your podcast
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6">
                  {isLoadingSummary ? (
                    <div className="flex flex-col items-center justify-center py-12">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="w-8 h-8 rounded-full border-4 border-muted border-t-primary mb-4"
                      />
                      <p className="text-sm text-muted-foreground">Generating summary...</p>
                    </div>
                  ) : summary ? (
                    <div className="space-y-6 text-foreground">
                      {summary.split(/\n\n+/).map((paragraph, idx) => {
                        const trimmed = paragraph.trim();
                        if (!trimmed) return null;
                        
                        // Check if it's a heading
                        if (trimmed.match(/^##\s+/)) {
                          const text = trimmed.replace(/^##\s+/, '');
                          return (
                            <h2 key={idx} className="text-xl font-semibold mt-8 mb-4 first:mt-0 text-foreground border-b border-border pb-2">
                              {text}
                            </h2>
                          );
                        }
                        if (trimmed.match(/^###\s+/)) {
                          const text = trimmed.replace(/^###\s+/, '');
                          return (
                            <h3 key={idx} className="text-lg font-semibold mt-6 mb-3 text-foreground">
                              {text}
                            </h3>
                          );
                        }
                        // Check if it's a numbered list
                        if (trimmed.match(/^\d+\.\s+/)) {
                          const items = trimmed.split(/\n/).filter(line => line.trim() && line.match(/^\d+\.\s+/));
                          return (
                            <ol key={idx} className="list-decimal list-inside space-y-2 ml-2">
                              {items.map((item, itemIdx) => {
                                const cleanItem = item.replace(/^\d+\.\s+/, '');
                                return (
                                  <li key={itemIdx} className="text-sm leading-relaxed text-foreground">
                                    {cleanItem}
                                  </li>
                                );
                              })}
                            </ol>
                          );
                        }
                        // Check if it's a bullet list
                        if (trimmed.match(/^[-*•]\s+/)) {
                          const items = trimmed.split(/\n/).filter(line => line.trim() && line.match(/^[-*•]\s+/));
                          return (
                            <ul key={idx} className="list-disc list-inside space-y-2 ml-2">
                              {items.map((item, itemIdx) => {
                                const cleanItem = item.replace(/^[-*•]\s+/, '');
                                return (
                                  <li key={itemIdx} className="text-sm leading-relaxed text-foreground">
                                    {cleanItem}
                                  </li>
                                );
                              })}
                            </ul>
                          );
                        }
                        // Regular paragraph
                        return (
                          <p key={idx} className="text-sm leading-relaxed text-foreground">
                            {trimmed}
                          </p>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No summary available. Please generate a script first.</p>
                    </div>
                  )}
                </div>
              </SheetContent>
            </Sheet>
            <Button variant="ghost" size="icon">
              <Share2 className="w-4 h-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={handleDownload}
              disabled={!audioUrl}
              title="Download MP3"
            >
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Podcast Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-center mb-8"
          >
            <h1 className="text-2xl md:text-3xl font-display font-bold mb-2">
              Your Generated Podcast
            </h1>
            <p className="text-muted-foreground">
              {links.length || 1} source{links.length !== 1 ? "s" : ""} • {formatTime(duration)}
            </p>
          </motion.div>

          {/* Waveform */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="w-full glass-card rounded-2xl p-8 mb-8"
          >
            <AudioWaveform isPlaying={isPlaying} />
          </motion.div>

          {/* Progress */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="w-full mb-8"
          >
            <ProgressBar
              progress={progress}
              duration={duration}
              onSeek={handleSeek}
            />
          </motion.div>

          {/* Hidden audio element */}
          {audioUrl && (
            <audio
              ref={audioRef}
              src={audioUrl}
              preload="metadata"
              style={{ display: "none" }}
            />
          )}

          {/* Controls */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center justify-center gap-4 mb-8"
          >
            <Button
              variant="ghost"
              size="icon"
              onClick={goToStart}
              className="text-muted-foreground hover:text-foreground"
            >
              <SkipBack className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={skipBackward}
              className="text-muted-foreground hover:text-foreground"
            >
              <RotateCcw className="w-5 h-5" />
              <span className="sr-only">-10s</span>
            </Button>
            <Button
              onClick={togglePlay}
              disabled={!audioUrl}
              variant="gradient"
              size="xl"
              className="w-16 h-16 rounded-full p-0"
            >
              {isPlaying ? (
                <Pause className="w-7 h-7" />
              ) : (
                <Play className="w-7 h-7 ml-1" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={skipForward}
              className="text-muted-foreground hover:text-foreground"
            >
              <RotateCw className="w-5 h-5" />
              <span className="sr-only">+10s</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={goToEnd}
              className="text-muted-foreground hover:text-foreground"
            >
              <SkipForward className="w-5 h-5" />
            </Button>
          </motion.div>

          {/* Speed & Volume */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center gap-6"
          >
            <SpeedControl speed={speed} onSpeedChange={setSpeed} />
            
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleMute}
                className="text-muted-foreground hover:text-foreground"
              >
                {isMuted ? (
                  <VolumeX className="w-5 h-5" />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </Button>
              <input
                type="range"
                min="0"
                max="100"
                value={isMuted ? 0 : volume}
                onChange={(e) => {
                  setVolume(parseInt(e.target.value));
                  setIsMuted(false);
                }}
                className="w-24 accent-primary"
              />
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Player;
