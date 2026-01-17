import { motion } from "framer-motion";

interface SpeedControlProps {
  speed: number;
  onSpeedChange: (speed: number) => void;
}

const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];

const SpeedControl = ({ speed, onSpeedChange }: SpeedControlProps) => {
  return (
    <div className="flex items-center gap-1 p-1 bg-muted rounded-lg">
      {speeds.map((s) => (
        <motion.button
          key={s}
          onClick={() => onSpeedChange(s)}
          className={`relative px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            speed === s ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          }`}
          whileTap={{ scale: 0.95 }}
        >
          {speed === s && (
            <motion.div
              layoutId="speed-indicator"
              className="absolute inset-0 bg-primary rounded-md"
              transition={{ type: "spring", duration: 0.4 }}
            />
          )}
          <span className="relative z-10">{s}x</span>
        </motion.button>
      ))}
    </div>
  );
};

export default SpeedControl;
