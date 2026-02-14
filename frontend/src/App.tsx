import React, { useState } from "react";
import Well from "./pages/Well";
import Welcome from "./components/Welcome";
import ChatScreen from "./components/ChatScreen";
import CursorDot from "./components/CursorDot";

type View = "welcome" | "dashboard" | "chat";

// Define the shape of the data we need to share
interface WellStats {
  minDepth: number;
  maxDepth: number;
  curves: string[];
}

const App: React.FC = () => {
  const [view, setView] = useState<View>("welcome");
  const [wellId, setWellId] = useState<string | null>(null);
  
  // NEW: Lifted state to share data between Dashboard and Chat
  const [wellStats, setWellStats] = useState<WellStats | null>(null);

  const appContainerStyle: React.CSSProperties = {
    width: "100%",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  };

  const navHeaderStyle: React.CSSProperties = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "1rem 2rem",
    borderBottom: "1px solid rgba(255,255,255,0.08)",
    background: "rgba(15, 23, 36, 0.8)",
    backdropFilter: "blur(10px)",
    position: "sticky",
    top: 0,
    zIndex: 50
  };

  return (
    <div style={appContainerStyle}>
      <CursorDot />

      {view !== "welcome" && (
        <div style={navHeaderStyle}>
          <div 
            style={{ fontWeight: "bold", fontSize: "1.2rem", cursor: 'pointer', color: 'white' }}
            onClick={() => setView("dashboard")}
          >
            Well Insights
          </div>
          <div>
            {view === "chat" && (
              <button className="btn secondary" onClick={() => setView("dashboard")}>
                ← Back to Dashboard
              </button>
            )}
          </div>
        </div>
      )}

      <div style={{ flex: 1, position: 'relative', width: "100%" }}>
        {view === "welcome" && (
          <Welcome onStart={() => setView("dashboard")} />
        )}

        <div style={{ display: view === "dashboard" ? "block" : "none" }}>
          <Well 
            initialWellId={wellId} 
            onWellIdChange={(id) => {
              setWellId(id);
              // Reset stats on new file
              setWellStats(null); 
            }}
            // NEW: Callback to save data
            onDataLoaded={(stats) => setWellStats(stats)}
          />
        </div>

        {view === "chat" && (
          <div style={{ padding: '20px', height: '100%' }}>
            <ChatScreen 
              wellId={wellId} 
              // NEW: Pass the stats to chat
              minDepth={wellStats?.minDepth}
              maxDepth={wellStats?.maxDepth}
              onBack={() => setView("dashboard")} 
            />
          </div>
        )}
      </div>

      {view === "dashboard" && (
        <button
          onClick={() => setView("chat")}
          style={{
            position: "fixed",
            bottom: "30px",
            right: "30px",
            width: "60px",
            height: "60px",
            borderRadius: "50%",
            background: "linear-gradient(135deg, #646cff, #535bf2)",
            color: "white",
            border: "none",
            fontSize: "24px",
            cursor: "pointer",
            zIndex: 9999,
            boxShadow: "0 8px 25px rgba(83,91,242,0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          💬
        </button>
      )}
    </div>
  );
};

export default App;