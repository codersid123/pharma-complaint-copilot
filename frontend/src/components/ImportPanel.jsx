import { useState } from "react";
import { importFile } from "../api";

export default function ImportPanel() {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const run = async (dryRun) => {
    setBusy(true);
    setError("");
    try {
      setReport(await importFile(file, dryRun));
    } catch (e) {
      setReport(null);
      setError(
        e.response?.data?.detail || "Upload failed. Is the backend running?",
      );
    } finally {
      setBusy(false);
    }
  };

  const pickFile = (e) => {
    setFile(e.target.files[0] || null);
    setReport(null); // a new file needs a new check
    setError("");
  };

  // "Import" is only allowed right after a successful check of this same file.
  const canImport = report?.dry_run && report.valid > 0 && !busy;

  return (
    <div className="card import-card">
      <div className="card-head">
        <div>
          <h1>Bulk Import</h1>
          <p className="sub">
            Upload a .csv or .xlsx file. Every row is checked with the same
            rules as the form.
          </p>
        </div>
      </div>

      <div className="import-controls">
        <input type="file" accept=".csv,.xlsx" onChange={pickFile} />
        <button
          className="btn-outline"
          disabled={!file || busy}
          onClick={() => run(true)}
        >
          1. Check file
        </button>
        <button
          className="btn-primary"
          disabled={!canImport}
          onClick={() => run(false)}
        >
          2. Import {report?.dry_run ? report.valid : ""} rows
        </button>
      </div>

      {error && <div className="banner-warn">{error}</div>}

      {report && (
        <>
          <div className="import-summary">
            <div>
              <strong>{report.total_rows}</strong>
              <span>rows read</span>
            </div>
            <div className="ok">
              <strong>{report.dry_run ? report.valid : report.imported}</strong>
              <span>{report.dry_run ? "ready to import" : "imported"}</span>
            </div>
            <div className="bad">
              <strong>{report.skipped}</strong>
              <span>skipped</span>
            </div>
          </div>

          {!report.dry_run && report.imported > 0 && (
            <p className="hint">
              Saved {report.complaint_numbers[0]} to{" "}
              {report.complaint_numbers.at(-1)}.
            </p>
          )}

          {report.ignored_columns.length > 0 && (
            <p className="hint">
              Ignored columns: {report.ignored_columns.join(", ")}
            </p>
          )}

          {report.errors.length > 0 && (
            <table className="error-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Field</th>
                  <th>Problem</th>
                </tr>
              </thead>
              <tbody>
                {report.errors.map((e, i) => (
                  <tr key={i}>
                    <td>{e.row}</td>
                    <td>{e.field}</td>
                    <td>{e.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
