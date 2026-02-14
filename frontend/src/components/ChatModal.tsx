import React from "react";
import ChatPanel from "./ChatPanel";

interface Props {
  open: boolean;
  onClose: () => void;
  wellId?: string | null;
}

const ChatModal: React.FC<Props> = ({ open, onClose, wellId }) => {
  if (!open) return null;

  return (
    <div className="chat-modal-overlay" onClick={onClose}>
      <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
        <div className="chat-modal-header">
          <strong>AI Chat</strong>
          <button className="btn secondary" onClick={onClose}>Close</button>
        </div>

        <div className="chat-modal-body">
          <ChatPanel wellId={wellId ?? undefined} selectedCurves={[]} />
        </div>
      </div>
    </div>
  );
};

export default ChatModal;
