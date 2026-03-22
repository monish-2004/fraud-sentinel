import axios from "axios";

const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE });

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const register = (userData) =>
  api.post("/api/auth/register", userData).then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });

export const login = (username, password) =>
  api.post("/api/auth/login", { username, password }).then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });

export const getCurrentUser = () =>
  api.get("/api/auth/me").then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
};

// Transaction endpoints
export const analyzeTransaction = (transaction) =>
  api.post("/api/analyze", transaction).then((r) => r.data);

export const analyzeText = (text) =>
  api.post("/api/analyze-text", { text }).then((r) => r.data);

export const generateTransactions = (count = 5, include_legitimate = true) =>
  api.post("/api/generate-transactions", { count, include_legitimate }).then((r) => r.data);

// PDF upload endpoint
export const uploadPDF = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  
  return api.post("/api/analyze-pdf", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  }).then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });
};

// Get report by ID
export const getReport = (reportId) =>
  api.get(`/api/report/${reportId}`).then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });

// Export report as PDF
export const exportReportToPDF = (reportId) =>
  api.get(`/api/report/${reportId}/export-pdf`, {
    responseType: 'blob',
  }).then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });

export const getDashboardStats = () =>
  api.get("/api/dashboard/stats").then((r) => r.data);

export const chatAboutTransaction = (transaction, analysis, conversationId, question) =>
  api.post("/api/chat", { 
    transaction, 
    analysis, 
    conversation_id: conversationId, 
    question 
  }).then((r) => r.data).catch((err) => {
    throw new Error(err.response?.data?.detail || err.message);
  });
