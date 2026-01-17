import { motion } from "framer-motion";

interface ProgressBarProps {
  progress: number;
  duration: number;
  onSeek: (progress: number) => void;
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const ProgressBar = ({ progress, duration, onSeek }: ProgressBarProps) => {
  const currentTime = (progress / 100) * duration;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = (x / rect.width) * 100;
    onSeek(Math.max(0, Math.min(100, percentage)));
  };

  return (
    <div className="w-full space-y-2">
      <div
        className="relative h-2 bg-muted rounded-full cursor-pointer group"
        onClick={handleClick}
      >
        <motion.div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-secondary rounded-full"
          style={{ width: `${progress}%` }}
          transition={{ duration: 0.1 }}
        />
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-foreground rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ left: `calc(${progress}% - 8px)` }}
        />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground font-medium">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>
    </div>
  );
};

export default ProgressBar;
