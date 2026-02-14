import React, { useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../../api/client";
import ReactMarkdown from "react-markdown";

function normalizeText(text: string) {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/^Curve:\s*(.*)$/gm, "## Curve: $1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}


interface Props {
  wellId: string;
  availableCurves: string[];
  minDepth: number;
  maxDepth: number;
}

const LogViewer: React.FC<Props> = ({
  wellId,
  availableCurves,
  minDepth,
  maxDepth,
}) => {
  const [selectedCurves, setSelectedCurves] = useState<string[]>([]);
  const [fromDepth, setFromDepth] = useState(minDepth);
  const [toDepth, setToDepth] = useState(maxDepth);

  const [plotData, setPlotData] = useState<any>(null);

  // 🧠 AI interpretation states
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const fetchPlotData = async () => {
    const res = await api.post("/query", {
      well_id: wellId,
      curves: selectedCurves,
      min_depth: fromDepth,
      max_depth: toDepth,
    });
    setPlotData(res.data);
  };

  const runInterpretation = async () => {
    setLoadingAI(true);
    setInterpretation(null);
    setAiError(null);

    try {
      const res = await api.post("/interpret", {
        well_id: wellId,
        curves: selectedCurves,
        min_depth: fromDepth,
        max_depth: toDepth,
      });

      setInterpretation(res.data.interpretation_text);
    } catch (err) {
      setAiError("Failed to generate AI interpretation");
    } finally {
      setLoadingAI(false);
    }
  };

  const traces =
    plotData &&
    Object.entries(plotData.curves).map(([curve, values]: any) => ({
      x: values,
      y: plotData.depths,
      type: "scatter",
      mode: "lines",
      name: curve,
    }));

  return (
    <div style={{ marginTop: 20 }}>
      <h3>Log Viewer</h3>

      {/* Curve selection */}
      <div>
        <strong>Select curves:</strong>
        {availableCurves.map((c) => (
          <label key={c} style={{ marginLeft: 10 }}>
            <input
              type="checkbox"
              value={c}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedCurves((prev) => [...prev, c]);
                } else {
                  setSelectedCurves((prev) =>
                    prev.filter((x) => x !== c)
                  );
                }
              }}
            />
            {c}
          </label>
        ))}
      </div>

      {/* Depth range */}
      <div style={{ marginTop: 10 }}>
        <label>
          From:
          <input
            type="number"
            value={fromDepth}
            onChange={(e) => setFromDepth(Number(e.target.value))}
          />
        </label>

        <label style={{ marginLeft: 10 }}>
          To:
          <input
            type="number"
            value={toDepth}
            onChange={(e) => setToDepth(Number(e.target.value))}
          />
        </label>

        <button onClick={fetchPlotData} style={{ marginLeft: 10 }}>
          Plot
        </button>

        <button
          onClick={runInterpretation}
          disabled={selectedCurves.length === 0}
          style={{ marginLeft: 10 }}
        >
          Run AI Interpretation
        </button>
      </div>

      {/* Plot */}
      {plotData && plotData.depths.length > 0 && (
        <Plot
          data={traces as any}
          layout={{
            title: "Well Logs vs Depth",
            yaxis: { autorange: "reversed", title: "Depth" },
            xaxis: { title: "Value" },
            height: 600,
          }}
          style={{ width: "100%" }}
          useResizeHandler
        />
      )}

      {/* AI Interpretation */}
      <div style={{ marginTop: 20 }}>
        <h3>AI Interpretation</h3>

        {loadingAI && <p>🤖 AI is analyzing the selected interval…</p>}

        {aiError && <p style={{ color: "red" }}>{aiError}</p>}

        {interpretation && (
          <div
            style={{
              background: "#f5f5f5",
              padding: 15,
              borderRadius: 6,
            }}
          >
            <ReactMarkdown>{normalizeText(interpretation)}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogViewer;
