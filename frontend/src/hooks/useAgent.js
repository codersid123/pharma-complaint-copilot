import { useDispatch, useSelector } from "react-redux";
import {
  applyAIPatch,
  addMessage,
  setProgress,
  setProcessing,
  setMissing,
  setRisk,
  setError,
  clearHighlights,
} from "../store/complaintSlice";
import * as api from "../api";

export function useAgent() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.complaint.form);

  const handle = async (call, userEcho) => {
    if (userEcho) dispatch(addMessage({ role: "user", text: userEcho }));
    dispatch(clearHighlights());
    dispatch(setProcessing(true));
    dispatch(setError(null));

    let pct = 0;
    const timer = setInterval(() => {
      pct = Math.min(pct + 3, 95);
      dispatch(setProgress(pct));
    }, 400);

    try {
      const data = await call();
      dispatch(applyAIPatch(data.patch));
      dispatch(addMessage({ role: "assistant", text: data.assistant_message }));
      dispatch(setMissing(data.missing_fields || []));
      if (data.risk) dispatch(setRisk(data.risk));
      dispatch(setProgress(100));
    } catch (e) {
      dispatch(setError(e.message));
      dispatch(
        addMessage({
          role: "assistant",
          text: "Something went wrong reaching the server. Is the backend running?",
        }),
      );
    } finally {
      clearInterval(timer);
      dispatch(setProcessing(false));
      setTimeout(() => dispatch(setProgress(0)), 1200);
    }
  };

  return {
    upload: (file) =>
      handle(() => api.uploadDocument(file), `Uploaded ${file.name}`),
    paste: (text) =>
      handle(() => api.submitText(text), "Pasted complaint text"),
    chat: (msg) => handle(() => api.askCopilot(msg, form), msg),
  };
}
