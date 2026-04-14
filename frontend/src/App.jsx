import { useState } from "react";
import DropZone from "./components/DropZone";
import Dashboard from "./components/Dashboard";
import { uploadXlsxForAnalysis } from "./api/prospect_analysis_api";

export default function App() {
  const [state, setState] = useState("idle"); // idle | loading | done | error
  const [result, setResult] = useState(null);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");

  const handleFile = async (file) => {
    setState("loading");
    setFileName(file.name);
    try {
      const data = await uploadXlsxForAnalysis(file);
      setResult(data);
      setState("done");
    } catch (e) {
      setError(e.message || "Error al procesar el archivo");
      setState("error");
    }
  };

  const reset = () => { setState("idle"); setResult(null); setFileName(""); setError(""); };

  return (
    <div className="app">
      {state === "idle" && (
        <div className="landing">
          <div className="landing-header">
            <h1 className="landing-title">ImporSan <span className="landing-accent">Market Analyzer</span></h1>
            <p className="landing-sub">Sube tu export de Helium 10 Xray (.xlsx) para ver el análisis completo del mercado</p>
          </div>
          <DropZone onFile={handleFile} />
          <p className="landing-hint">Secciones: Tamaño · HHI · Competidores · Frescura · Márgenes · Orígenes · MEFS Score</p>
        </div>
      )}

      {state === "loading" && (
        <div className="loading-screen">
          <div className="spinner" />
          <p>Analizando <strong>{fileName}</strong>…</p>
        </div>
      )}

      {state === "error" && (
        <div className="error-screen">
          <p className="error-icon">⚠️</p>
          <p>{error}</p>
          <button className="btn-reset" onClick={reset}>Intentar de nuevo</button>
        </div>
      )}

      {state === "done" && result && (
        <Dashboard data={result} fileName={fileName} onReset={reset} />
      )}
    </div>
  );
}
