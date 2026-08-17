import { createSlice } from "@reduxjs/toolkit";

export const FIELDS = [
  "complaint_source",
  "customer_name",
  "product_name",
  "product_strength",
  "batch_number",
  "manufacturing_date",
  "expiry_date",
  "quantity_affected",
  "complaint_type",
  "complaint_date",
  "complaint_description",
  "initial_severity",
  "priority",
];

const emptyForm = Object.fromEntries(FIELDS.map((f) => [f, ""]));

const initialState = {
  form: emptyForm,
  aiFilledFields: [],
  history: [],
  messages: [
    {
      role: "assistant",
      text: "Upload a complaint document or paste text above. I will extract the details and populate the form for you.",
    },
  ],
  extractionProgress: 0,
  isProcessing: false,
  missingFields: [],
  risk: null,
  saved: null,
  error: null,
};

const slice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    applyAIPatch: (s, a) => {
      const { updates = {}, clear = [] } = a.payload;
      s.history.push({ ...s.form });
      Object.entries(updates).forEach(([k, v]) => {
        if (FIELDS.includes(k) && v !== null && v !== "") {
          s.form[k] = String(v);
          if (!s.aiFilledFields.includes(k)) s.aiFilledFields.push(k);
        }
      });
      clear.forEach((k) => {
        if (FIELDS.includes(k)) s.form[k] = "";
      });
    },
    undo: (s) => {
      const prev = s.history.pop();
      if (prev) s.form = prev;
    },
    addMessage: (s, a) => {
      s.messages.push(a.payload);
    },
    setProgress: (s, a) => {
      s.extractionProgress = a.payload;
    },
    setProcessing: (s, a) => {
      s.isProcessing = a.payload;
    },
    setMissing: (s, a) => {
      s.missingFields = a.payload;
    },
    setRisk: (s, a) => {
      s.risk = a.payload;
    },
    setSaved: (s, a) => {
      s.saved = a.payload;
    },
    setError: (s, a) => {
      s.error = a.payload;
    },
    clearHighlights: (s) => {
      s.aiFilledFields = [];
    },
    resetForm: () => initialState,
  },
});

export const {
  applyAIPatch,
  undo,
  addMessage,
  setProgress,
  setProcessing,
  setMissing,
  setRisk,
  setSaved,
  setError,
  clearHighlights,
  resetForm,
} = slice.actions;

export default slice.reducer;
