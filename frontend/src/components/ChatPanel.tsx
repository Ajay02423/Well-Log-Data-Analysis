import React, { useState, useRef, useEffect } from "react";
import { api } from "../api/client";
import ReactMarkdown from "react-markdown";

interface Props {
  wellId?: string;
  selectedCurves: string[];
  minDepth?: number;
  maxDepth?: number;
}

const ChatPanel: React.FC<Props> = ({
  wellId,
  selectedCurves,
  minDepth,
  maxDepth,
}) => {
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; text: string }[]>([
    { role: "assistant", text: "Hello! I have analyzed your well data. Ask me anything about curves, lithology, or trends." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const convKey = wellId ? `well_chat_conv_${wellId}` : undefined;

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Expand Textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setMessages((m) => [...m, { role: "user", text: userMsg }]);
    setInput("");
    
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    
    setLoading(true);

    try {
      const conversation_id = convKey ? sessionStorage.getItem(convKey) || undefined : undefined;

      const res = await api.post("/chat", {
        question: userMsg,
        well_id: wellId,
        selected_curves: selectedCurves,
        min_depth: minDepth,
        max_depth: maxDepth,
        conversation_id,
      });

      if (res.data && res.data.conversation_id && convKey) {
        sessionStorage.setItem(convKey, res.data.conversation_id);
      }

      setMessages((m) => [...m, { role: "assistant", text: res.data.answer }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Messages List */}
      <div className="chat-history">
        {messages.map((m, i) => (
          // IMPORTANT: This class structure must match App.css
          <div key={i} className={`message-wrapper ${m.role}`}>
            <span className="chat-role-label">{m.role === "user" ? "You" : "AI Assistant"}</span>
            <div className="chat-bubble">
              <ReactMarkdown>{m.text}</ReactMarkdown>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message-wrapper assistant">
            <span className="chat-role-label">AI Assistant</span>
            <div className="chat-bubble" style={{ fontStyle: 'italic', opacity: 0.7 }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Type your message here..."
          disabled={loading}
        />
        <button 
          className="btn primary" 
          onClick={sendMessage} 
          disabled={loading || !input.trim()}
          style={{ height: 'fit-content' }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;