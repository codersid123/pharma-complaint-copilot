import { useState } from "react";
import ComplaintForm from "./components/ComplaintForm";
import CopilotPanel from "./components/CopilotPanel";
import ImportPanel from "./components/ImportPanel";

export default function App() {
  const [page, setPage] = useState("intake");

  return (
    <>
      <nav className="tabs">
        <button
          className={page === "intake" ? "active" : ""}
          onClick={() => setPage("intake")}
        >
          New complaint
        </button>
        <button
          className={page === "import" ? "active" : ""}
          onClick={() => setPage("import")}
        >
          Bulk import
        </button>
      </nav>

      {page === "intake" ? (
        <div className="layout">
          <ComplaintForm />
          <CopilotPanel />
        </div>
      ) : (
        <div className="layout-single">
          <ImportPanel />
        </div>
      )}
    </>
  );
}
