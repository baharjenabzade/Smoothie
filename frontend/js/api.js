const BASE = "/api/v1";
const TOKEN_KEY = "ielts_token";

let token = null;
try {
  token = localStorage.getItem(TOKEN_KEY);
} catch {
  /* storage can be blocked; the session then lasts until the tab closes */
}

let unauthorizedHandler = () => {};

export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

export function getToken() {
  return token;
}

export function setToken(value) {
  token = value || null;
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function describe(data) {
  if (!data || data.detail === undefined) return null;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((e) => {
        const field = Array.isArray(e.loc) ? e.loc.filter((p) => p !== "body").join(".") : "";
        const msg = String(e.msg || "Invalid value").replace(/^Value error, /, "");
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }
  return null;
}

async function request(method, path, { body, form, params } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== null && value !== undefined && value !== "") url.searchParams.set(key, value);
  }
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const init = { method, headers };
  if (form) init.body = new URLSearchParams(form);
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new ApiError("Cannot reach the server. Check that the API is running.", 0);
  }
  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    /* non-JSON error body */
  }
  if (!response.ok) {
    if (response.status === 401 && token && path !== "/auth/login") {
      setToken(null);
      unauthorizedHandler();
    }
    throw new ApiError(describe(data) || `Request failed (${response.status}).`, response.status);
  }
  return data;
}

const get = (path, params) => request("GET", path, { params });
const post = (path, body) => request("POST", path, { body });

export const api = {
  // auth
  register: (body) => post("/auth/register", body),
  login: (email, password) => request("POST", "/auth/login", { form: { username: email, password } }),
  me: () => get("/auth/me"),
  updateMe: (body) => request("PATCH", "/auth/me", { body }),
  // questions
  topics: () => get("/questions/topics"),
  questions: (params) => get("/questions", params),
  randomQuestion: (params) => get("/questions/random", params),
  generateQuestions: (body) => post("/questions/generate", body),
  // practice
  createSession: (body) => post("/practice/sessions", body),
  sessions: (params) => get("/practice/sessions", params),
  session: (id) => get(`/practice/sessions/${id}`),
  deleteSession: (id) => request("DELETE", `/practice/sessions/${id}`),
  submitAnswer: (sessionId, body) => post(`/practice/sessions/${sessionId}/answers`, body),
  sampleAnswer: (body) => post("/practice/sample-answer", body),
  followUp: (body) => post("/practice/follow-up", body),
  // learning
  vocabulary: (params) => get("/learning/vocabulary", params),
  deleteVocabulary: (id) => request("DELETE", `/learning/vocabulary/${id}`),
  topicVocabulary: (body) => post("/learning/topic-vocabulary", body),
  grammarIssues: (params) => get("/learning/grammar-issues", params),
  weaknesses: () => get("/learning/weaknesses"),
  recommendations: () => get("/learning/recommendations"),
  // clusters and stories
  clusters: () => get("/clusters"),
  stories: () => get("/stories"),
  createStory: (body) => post("/stories", body),
  updateStory: (id, body) => request("PUT", `/stories/${id}`, { body }),
  deleteStory: (id) => request("DELETE", `/stories/${id}`),
  storyMatches: (id) => get(`/stories/${id}/matches`),
  suggestStories: (questionId) => get("/stories/suggest", { question_id: questionId }),
  adaptStory: (id, questionId) => post(`/stories/${id}/adapt`, { question_id: questionId }),
  // groups, import, similar questions
  groups: () => get("/groups"),
  group: (id, part) => get(`/groups/${id}`, { part }),
  createGroup: (body) => post("/groups", body),
  updateGroup: (id, body) => request("PUT", `/groups/${id}`, { body }),
  deleteGroup: (id) => request("DELETE", `/groups/${id}`),
  importQuestions: (body) => post("/questions/import", body),
  questionGroups: (params) => get("/questions/groups", params),
  similarQuestions: (id) => get(`/questions/${id}/similar`),
  // dashboard
  dashboard: () => get("/dashboard"),
};
