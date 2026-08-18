import { useSelector, useDispatch } from "react-redux";
import AIField from "./AIField";
import { resetForm } from "../store/complaintSlice";
import { saveComplaint, checkDuplicate } from "../api";

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const { form, risk, missingFields } = useSelector((s) => s.complaint);
  const canSave = missingFields.length === 0 && form.customer_name;

  const onSave = async () => {
    const { duplicates } = await checkDuplicate(form);
    if (duplicates.length > 0) {
      const list = duplicates.map((d) => d.complaint_number).join(", ");
      if (
        !window.confirm(
          `Batch ${form.batch_number} already has ${duplicates.length} logged complaint(s): ${list}.\n\nSave anyway?`,
        )
      )
        return;
    }
    const res = await saveComplaint(form, risk);
    alert(`Saved as ${res.complaint_number}`);
  };

  return (
    <div className="card">
      <div className="card-head">
        <div>
          <h1>Log Customer Complaint</h1>
          <p className="sub">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className="chip">Pending Triage</span>
      </div>

      <h2 className="section">1. Origin &amp; Customer Details</h2>
      <div className="grid">
        <AIField label="Complaint Source" name="complaint_source" />
        <AIField label="Customer Name" name="customer_name" />
      </div>

      <h2 className="section">2. Product &amp; Batch Identification</h2>
      <div className="grid">
        <AIField label="Product Name" name="product_name" />
        <AIField label="Product Strength/Grade" name="product_strength" />
        <AIField label="Batch/Lot Number" name="batch_number" />
        <AIField label="Manufacturing Date" name="manufacturing_date" />
        <AIField label="Expiry Date" name="expiry_date" />
        <AIField label="Quantity Affected" name="quantity_affected" unit="kg" />
      </div>

      <h2 className="section">3. Complaint Details</h2>
      <div className="grid">
        <AIField label="Complaint Type" name="complaint_type" />
        <AIField label="Complaint Date" name="complaint_date" />
      </div>
      <AIField
        label="Detailed Complaint Description"
        name="complaint_description"
        textarea
      />

      <h2 className="section">4. Initial Assessment &amp; Priority</h2>
      <div className="grid">
        <AIField label="Initial Severity" name="initial_severity" />
        <AIField label="Priority" name="priority" />
      </div>

      {missingFields.length > 0 && (
        <div className="banner-warn">
          {missingFields.length} field(s) still needed. Ask the copilot to fill
          them.
        </div>
      )}

      <div className="actions">
        <button className="btn-ghost" onClick={() => dispatch(resetForm())}>
          ↺ Reset Form
        </button>
        <button className="btn-primary" disabled={!canSave} onClick={onSave}>
          Save Complaint
        </button>
      </div>
    </div>
  );
}
