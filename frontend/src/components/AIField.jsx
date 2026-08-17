import { useSelector, useDispatch } from "react-redux";
import { addMessage } from "../store/complaintSlice";

const LABEL_HINT = {
  batch_number: "set batch number to APX-2451",
  initial_severity: "change severity to Critical",
  customer_name: "the customer is MedLife Distributors",
};

export default function AIField({ label, name, textarea = false, unit }) {
  const dispatch = useDispatch();
  const value = useSelector((s) => s.complaint.form[name]);
  const isNew = useSelector((s) => s.complaint.aiFilledFields.includes(name));
  const isMissing = useSelector((s) =>
    s.complaint.missingFields.includes(name),
  );

  const nudge = () =>
    dispatch(
      addMessage({
        role: "assistant",
        text: `"${label}" is managed by me — the form is read-only by design. Try: "${LABEL_HINT[name] || `set ${label.toLowerCase()} to ...`}"`,
      }),
    );

  const cls = `ai-input${isNew ? " ai-filled" : ""}${isMissing ? " ai-missing" : ""}`;
  const props = {
    value: value || "",
    readOnly: true,
    tabIndex: -1,
    onClick: nudge,
    placeholder: "Awaiting AI extraction...",
    className: cls,
  };

  return (
    <div className={`field${textarea ? " field-full" : ""}`}>
      <label>{label}</label>
      <div className="input-wrap">
        {textarea ? <textarea rows={3} {...props} /> : <input {...props} />}
        {unit && <span className="unit">{unit}</span>}
      </div>
    </div>
  );
}
