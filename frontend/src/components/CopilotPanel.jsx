import { useState, useRef, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useAgent } from "../hooks/useAgent";
import { undo } from "../store/complaintSlice";

export default function CopilotPanel() {
  const [input, setInput] = useState("");
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const dispatch = useDispatch();
  const agent = useAgent();
  const { messages, extractionProgress, isProcessing, risk } = useSelector(
    (s) => s.complaint,
  );
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) agent.upload(file);
  };

  const send = () => {
    if (!input.trim() || isProcessing) return;
    agent.chat(input.trim());
    setInput("");
  };

  return (
    <div className="card copilot">
      <div className="card-head">
        <h2>✦ AI Complaint Intake Assistant</h2>
        <span className="chip beta">BETA</span>
      </div>

      <div
        className="dropzone"
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <input
          type="file"
          id="fileInput"
          hidden
          accept=".pdf,.docx,.txt,.eml"
          onChange={(e) => e.target.files[0] && agent.upload(e.target.files[0])}
        />
        <p>Drag &amp; drop complaint document here</p>
        <label htmlFor="fileInput" className="link">
          or click to browse
        </label>
      </div>

      <div className="or">OR</div>

      {!pasteMode ? (
        <button className="btn-outline" onClick={() => setPasteMode(true)}>
          Paste Complaint Text / Email
        </button>
      ) : (
        <div>
          <textarea
            rows={5}
            className="paste"
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste the complaint email here..."
          />
          <button
            className="btn-outline"
            onClick={() => {
              agent.paste(pasteText);
              setPasteMode(false);
            }}
          >
            Extract
          </button>
        </div>
      )}

      <div className="banner-info">
        Supported: PDF, DOCX, TXT, EML · Max 10MB
      </div>

      {extractionProgress > 0 && (
        <div className="progress-block">
          <div className="progress-head">
            <span>EXTRACTION PROGRESS</span>
            <span>{extractionProgress}%</span>
          </div>
          <div className="bar">
            <div className="fill" style={{ width: `${extractionProgress}%` }} />
          </div>
          <p className="hint">
            Analyzing document content and extracting key details...
          </p>
        </div>
      )}

      {risk && (
        <div className={`risk risk-${risk.level.toLowerCase()}`}>
          <strong>
            AI Risk Assessment — {risk.level} ({risk.score}/100)
          </strong>
          <p>{risk.rationale}</p>
          <p className="rec">→ {risk.recommended_action}</p>
        </div>
      )}

      <div className="chat">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="composer">
        <input
          value={input}
          placeholder="Ask me anything about this complaint..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button onClick={send} disabled={isProcessing}>
          ➤
        </button>
      </div>
      <button className="btn-link" onClick={() => dispatch(undo())}>
        Undo last change
      </button>
      <p className="disclaimer">
        AI responses may contain errors. Please verify information.
      </p>
    </div>
  );
}
