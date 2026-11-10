import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

export const uploadDocument = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api
    .post("/intake/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const submitText = (text) =>
  api.post("/intake/text", { text }).then((r) => r.data);

export const askCopilot = (message, current_form) =>
  api.post("/copilot/chat", { message, current_form }).then((r) => r.data);

export const saveComplaint = (form, risk) =>
  api.post("/complaints", { form, risk }).then((r) => r.data);

export const checkDuplicate = (form) =>
  api.post("/complaints/check-duplicate", { form }).then((r) => r.data);

export const importFile = (file, dryRun) => {
  const fd = new FormData();
  fd.append("file", file);
  return api
    .post(`/import?dry_run=${dryRun}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};
