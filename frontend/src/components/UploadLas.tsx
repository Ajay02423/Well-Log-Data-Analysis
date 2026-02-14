import React, { useState } from "react";
import { api } from "../api/client";

interface Props {
  onUploaded: (wellId: string) => void;
  isCompact?: boolean;
}

const UploadLas: React.FC<Props> = ({ onUploaded, isCompact = false }) => {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    try {
      const res = await api.post("/upload-las", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onUploaded(res.data.well_id);
    } catch (err) {
      alert("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  // Inline styles to guarantee appearance
  const labelStyle: React.CSSProperties = isCompact
    ? {
        // Compact Style (Dashboard Header)
        display: "inline-flex",
        alignItems: "center",
        padding: "0.5rem 1rem",
        border: "1px solid #646cff",
        borderRadius: "8px",
        cursor: "pointer",
        color: "#646cff",
        fontSize: "0.9rem",
        backgroundColor: "transparent"
      }
    : {
        // Big Style (Center Screen)
        display: "inline-block",
        padding: "1rem 2rem",
        backgroundColor: "#646cff",
        color: "white",
        borderRadius: "8px",
        cursor: "pointer",
        fontSize: "1.1rem",
        fontWeight: "bold",
        boxShadow: "0 4px 15px rgba(100, 108, 255, 0.4)"
      };

  return (
    <div style={{ display: 'inline-block' }}>
      <label style={labelStyle}>
        <span>{loading ? "Uploading..." : isCompact ? "Change File" : "📁 Upload LAS File"}</span>
        <input 
          type="file" 
          accept=".las" 
          onChange={handleUpload} 
          style={{ display: "none" }} 
          disabled={loading}
        />
      </label>
    </div>
  );
};

export default UploadLas;