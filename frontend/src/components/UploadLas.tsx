import React, { useState } from "react";
import { api } from "../api/client";

interface Props {
  onUploaded: (wellId: string) => void;
  isCompact?: boolean;
}

const UploadLas: React.FC<Props> = ({ onUploaded, isCompact = false }) => {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    // 1. Basic validation
    if (!e.target.files?.length) return;
    const file = e.target.files[0];

    // Reset input so the same file can be selected again if needed
    e.target.value = ""; 

    setLoading(true);

    try {
      // ==========================================
      // Step 1: Get Presigned URL
      // ==========================================
      // We encode the filename to handle spaces or special characters safely
      const presignRes = await api.post(
        `/presign-upload?filename=${encodeURIComponent(file.name)}`
      );

      const { upload_url, s3_key } = presignRes.data;

      // ==========================================
      // Step 2: Upload to S3
      // ==========================================
      // IMPORTANT: Use standard 'fetch' here instead of 'api' (axios).
      // Axios interceptors might add Authorization headers (Bearer token),
      // which will cause AWS S3 to reject the upload with a 403 or 400 error.
      const s3Response = await fetch(upload_url, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": "application/octet-stream",
        },
      });

      if (!s3Response.ok) {
        throw new Error(`S3 Upload failed: ${s3Response.statusText}`);
      }

      // ==========================================
      // Step 3: Confirm with Backend
      // ==========================================
      // FIX: Your backend expects 's3_key' as a query parameter (in the URL).
      // sending it in the body {} would cause a 422 error.
      const confirmRes = await api.post(
        `/confirm-upload?s3_key=${encodeURIComponent(s3_key)}`
      );

      // Pass the new well ID back to the parent component
      onUploaded(confirmRes.data.well_id);

    } catch (err: any) {
      console.error("Upload process failed:", err);
      // Show a more specific error message if available
      alert(err.response?.data?.detail || err.message || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  // Styles based on 'isCompact' prop
  const labelStyle: React.CSSProperties = isCompact
    ? {
        display: "inline-flex",
        alignItems: "center",
        padding: "0.5rem 1rem",
        border: "1px solid #646cff",
        borderRadius: "8px",
        cursor: loading ? "not-allowed" : "pointer",
        color: "#646cff",
        fontSize: "0.9rem",
        backgroundColor: "transparent",
        opacity: loading ? 0.7 : 1,
      }
    : {
        display: "inline-block",
        padding: "1rem 2rem",
        backgroundColor: "#646cff",
        color: "white",
        borderRadius: "8px",
        cursor: loading ? "not-allowed" : "pointer",
        fontSize: "1.1rem",
        fontWeight: "bold",
        boxShadow: "0 4px 15px rgba(100, 108, 255, 0.4)",
        opacity: loading ? 0.7 : 1,
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