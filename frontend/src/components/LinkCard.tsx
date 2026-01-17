import { motion } from "framer-motion";
import { FileText, Video, Link as LinkIcon, X } from "lucide-react";

interface LinkCardProps {
  url: string;
  type: "article" | "pdf" | "video" | "link";
  onRemove: () => void;
  index: number;
}

const typeConfig = {
  article: { icon: FileText, label: "Article" },
  pdf: { icon: FileText, label: "PDF" },
  video: { icon: Video, label: "Video" },
  link: { icon: LinkIcon, label: "Link" },
};

const LinkCard = ({ url, type, onRemove, index }: LinkCardProps) => {
  const config = typeConfig[type];
  const Icon = config.icon;

  const getDomain = (url: string) => {
    try {
      return new URL(url).hostname.replace("www.", "");
    } catch {
      return url;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, y: -10 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="glass-card rounded-xl p-4 group relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        
        <div className="flex-1 min-w-0">
          <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-primary/10 text-primary mb-1">
            {config.label}
          </span>
          <p className="text-sm text-foreground truncate">{getDomain(url)}</p>
          <p className="text-xs text-muted-foreground truncate mt-0.5">{url}</p>
        </div>
        
        <button
          onClick={onRemove}
          className="flex-shrink-0 w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-destructive/20 hover:text-destructive"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
};

export default LinkCard;
