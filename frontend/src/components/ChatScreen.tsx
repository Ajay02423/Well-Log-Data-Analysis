import React from "react";
import ChatPanel from "./ChatPanel";

interface Props {
  wellId?: string | null;
  minDepth?: number;
  maxDepth?: number;
  onBack: () => void;
}

const ChatScreen: React.FC<Props> = ({ wellId, minDepth, maxDepth }) => {
  return (
    <div style={{ width: '100%', height: '100%', paddingTop: '10px' }}>
      <ChatPanel 
        wellId={wellId ?? undefined} 
        selectedCurves={[]} 
        minDepth={minDepth}
        maxDepth={maxDepth}
      />
    </div>
  );
};

export default ChatScreen;