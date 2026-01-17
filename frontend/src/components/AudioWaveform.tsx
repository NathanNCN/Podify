import { motion } from "framer-motion";

interface AudioWaveformProps {
  isPlaying: boolean;
}

const AudioWaveform = ({ isPlaying }: AudioWaveformProps) => {
  const bars = 40;

  return (
    <div className="flex items-center justify-center gap-1 h-24">
      {Array.from({ length: bars }).map((_, i) => {
        const delay = i * 0.05;
        const height = 20 + Math.sin(i * 0.5) * 40 + Math.random() * 20;

        return (
          <motion.div
            key={i}
            className="w-1 rounded-full bg-gradient-to-t from-primary to-secondary"
            initial={{ height: 4 }}
            animate={
              isPlaying
                ? {
                    height: [height * 0.3, height, height * 0.5, height * 0.8, height * 0.3],
                  }
                : { height: 4 }
            }
            transition={
              isPlaying
                ? {
                    duration: 0.8 + Math.random() * 0.4,
                    repeat: Infinity,
                    delay: delay,
                    ease: "easeInOut",
                  }
                : { duration: 0.3 }
            }
          />
        );
      })}
    </div>
  );
};

export default AudioWaveform;
