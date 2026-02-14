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

    const file = e.target.files[0];
    setLoading(true);

    try {
      // 1️⃣ Ask backend for presigned URL
      const presignRes = await api.post(
        `/presign-upload?filename=${encodeURIComponent(file.name)}`
      );

      const { upload_url, s3_key } = presignRes.data;

      // 2️⃣ Upload file directly to S3
      await fetch(upload_url, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": "application/octet-stream",
        },
      });

      // 3️⃣ Tell backend upload is done (creates well + starts ingestion)
      const confirmRes = await api.post("/confirm-upload", {
        s3_key,
      });

      // 🔑 This well_id is what progress bar uses
      onUploaded(confirmRes.data.well_id);

    } catch (err) {
      console.error(err);
      alert("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const labelStyle: React.CSSProperties = isCompact
    ? {
        display: "inline-flex",
        alignItems: "center",
        padding: "0.5rem 1rem",
        border: "1px solid #646cff",
        borderRadius: "8px",
        cursor: "pointer",
        color: "#646cff",
        fontSize: "0.9rem",
        backgroundColor: "transparent",
      }
    : {
        display: "inline-block",
        padding: "1rem 2rem",
        backgroundColor: "#646cff",
        color: "white",
        borderRadius: "8px",
        cursor: "pointer",
        fontSize: "1.1rem",
        fontWeight: "bold",
        boxShadow: "0 4px 15px rgba(100, 108, 255, 0.4)",
      };

  return (
    <div style={{ display: "inline-block" }}>
      <label style={labelStyle}>
        <span>
          {loading
            ? "Uploading..."
            : isCompact
            ? "Change File"
            : "📁 Upload LAS File"}
        </span>
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
