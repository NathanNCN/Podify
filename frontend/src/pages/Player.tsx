import { useState, useEffect } from "react";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import AudioWaveform from "@/components/AudioWaveform";
import ProgressBar from "@/components/ProgressBar";
import SpeedControl from "@/components/SpeedControl";
import { ExtractedContent } from "@/lib/api";

interface LinkItem {
  id: string;
  url: string;
  type: "article" | "pdf" | "video" | "link";
}

const Player = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [volume, setVolume] = useState(80);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const links: LinkItem[] = location.state?.links || [];
  const extractedContents: ExtractedContent[] = location.state?.extractedContents || [];

  const duration = 12 * 60 + 34; // 12:34 demo duration

  // Initialize player - no need to redirect, just show the player
  useEffect(() => {
    setIsLoading(false);
  }, []);

  // Simulate playback
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setIsPlaying(false);
          return 100;
        }
        return prev + (100 / duration) * speed;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, speed, duration]);

  const togglePlay = () => setIsPlaying(!isPlaying);

  const skipForward = () => {
    setProgress((prev) => Math.min(100, prev + (10 / duration) * 100));
  };

  const skipBackward = () => {
    setProgress((prev) => Math.max(0, prev - (10 / duration) * 100));
  };

  const goToStart = () => {
    setProgress(0);
  };

  const goToEnd = () => {
    setProgress(100);
    setIsPlaying(false);
  };

  const toggleMute = () => setIsMuted(!isMuted);

  if (isLoading) {
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
            Generating Your Podcast
          </h2>
          <p className="text-muted-foreground">
            AI is processing your content...
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
            <Button variant="ghost" size="icon">
              <Share2 className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon">
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
              {location.state?.links?.length || 1} sources • 12 min 34 sec
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
              onSeek={setProgress}
            />
          </motion.div>

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
