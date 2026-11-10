# AI-Powered Customer Complaint Management System

A pharmaceutical QMS complaint intake and triage module for API & FDF manufacturing.

**The form is entirely AI-driven.** Every field is read-only; values are populated
either by extracting an uploaded complaint document or by natural-language instruction
to the copilot. There is no manual data entry path — which means every value in the
record traces back to a source document or an explicit instruction, giving an audit
trail in the spirit of 21 CFR Part 11.

## Stack
React 18 + Redux Toolkit · FastAPI · LangGraph · Groq · PostgreSQL · Inter


# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Model Selection Note

The assignment specifies `gemma2-9b-it` on Groq. Groq deprecated this model
in August 2025 and removed it from service; the suggested alternative
`llama-3.3-70b-versatile` is also no longer available on GroqCloud.

Verified against the live models endpoint (see `backend/check_models.py`).

The application therefore queries `GET /openai/v1/models` at startup and selects
the first available model from a configured preference list. `GROQ_MODEL` is
still set to `gemma2-9b-it` in `.env` — if Groq restores it, the app will use it
with no code change.

Currently resolving to:
- Routing / lightweight tasks: `openai/gpt-oss-20b`
- Extraction, modification, risk assessment: `openai/gpt-oss-120b`