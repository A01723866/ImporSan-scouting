import { useRef, useState } from "react";

export default function DropZone({ onFile }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const processFile = (file) => {
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "xlsx" && ext !== "xls") {
      alert("Solo se aceptan archivos .xlsx");
      return;
    }
    onFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    processFile(file);
  };

  const handleChange = (e) => {
    processFile(e.target.files[0]);
  };

  return (
    <div
      className={`dropzone${dragging ? " dropzone--active" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        onChange={handleChange}
        style={{ display: "none" }}
      />
      <p className="dropzone-icon">📂</p>
      <p className="dropzone-text">Arrastra tu archivo <strong>.xlsx</strong> aquí</p>
      <p className="dropzone-sub">o haz clic para seleccionarlo</p>
    </div>
  );
}
