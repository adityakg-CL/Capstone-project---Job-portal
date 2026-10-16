// Centralized API client for CirrusLabs TalentHub.
// Uses VITE_API_BASE_URL which already includes /api/v1 exactly once.
// No secrets are stored here; the bearer token is kept in localStorage only so
// that Authorization headers survive page reloads. The backend also sets an
// HTTP-only cookie, and the backend token remains the single source of truth.
const RAW_BASE = import.meta.env.VITE_API_BASE_URL as string | undefined;

function normalizeBase(raw: string | undefined): string {
  // Match the port the backend is actually configured to run on.
  const fallback = "http://localhost:8001/api/v1";
  const value = (raw ?? fallback).trim();
  // Remove trailing slashes only; do NOT append /api/v1 (already included).
  return value.replace(/\/+$/, "");
}

export const API_BASE_URL = normalizeBase(RAW_BASE);


export type BackendRole = "employee" | "hiring_manager" | "hr_admin";
export type JobStatus = "open" | "closed";

export interface ApiUser {
  id: string;
  full_name: string;
  email: string;
  role: BackendRole;
  title?: string | null;
  team?: string | null;
  location?: string | null;
  phone?: string | null;
  skills?: string[];
  avatar?: ApiAvatar | null;
}

export interface ApiAvatar {
  filename: string | null;
  content_type: string | null;
  size_bytes: number | null;
  uploaded_at: string | null;
}

export interface ApiJob {
  id: string;
  title: string;
  team: string;
  location: string;
  employment_type?: string;
  experience?: string;
  salary_band?: string;
  description?: string;
  skills?: string[];
  status: JobStatus;
  owner_id?: string;
  applicant_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface JobCreatePayload {
  title: string;
  team: string;
  location: string;
  employment_type: string;
  experience: string;
  salary_band: string;
  description: string;
  skills: string[];
}

export interface JobUpdatePayload {
  title?: string;
  team?: string;
  location?: string;
  employment_type?: string;
  experience?: string;
  salary_band?: string;
  description?: string;
  skills?: string[];
}


export interface ApiApplication {
  id: string;
  job_id: string;
  job_title: string;
  employee_id: string;
  applicant?: {
    id: string;
    full_name: string | null;
    email: string | null;
    title?: string | null;
    team?: string | null;
  } | null;
  status: string;
  cover_note?: string;
  status_history?: Array<{ status: string; actor_id?: string; at?: string; reason?: string | null }>;
  created_at?: string;
  updated_at?: string;
}

export interface ApiResume {
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface ApiProfile extends ApiUser {
  created_at?: string;
  resume?: ApiResume | null;
}

export interface ApiPersonRef {
  id: string | null;
  full_name: string | null;
  email?: string | null;
  title?: string | null;
  team?: string | null;
}

export interface ApiBonusSummary {
  id: string;
  approval_status: string | null;
  payment_status: string | null;
  amount?: number | null;
  currency?: string | null;
}

export interface ApiReferral {
  id: string;
  referrer_id: string;
  referrer?: ApiPersonRef | null;
  candidate_name: string;
  candidate_email: string;
  job_id?: string | null;
  job_title?: string | null;
  status: string;
  note?: string | null;
  eligibility_reason?: string | null;
  status_history?: Array<{ status: string; actor_id?: string; at?: string; reason?: string | null }>;
  bonus?: ApiBonusSummary | null;
  created_at?: string;
  updated_at?: string;
}

export interface ApiBonus {
  id: string;
  referral_id: string;
  referrer_id: string;
  approval_status: string;
  payment_status: string;
  amount?: number | null;
  currency?: string;
  reason?: string | null;
  payment_reference?: string | null;
  candidate_name?: string | null;
  job_id?: string | null;
  referral_status?: string | null;
  referrer?: ApiPersonRef | null;
  created_at?: string;
  updated_at?: string;
}


export interface ReferralsResponse {
  items: ApiReferral[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
}

export interface BonusesResponse {
  items: ApiBonus[];
  page?: number;
  page_size?: number;
  total?: number;
  total_pages?: number;
}

export interface ManagedJobsResponse {
  items: ApiJob[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
}


export interface EmployeeDashboardData {
  applications_total: number;
  applications_active: number;
  referrals_total: number;
  referrals_pending: number;
  open_jobs: number;
  unread_notifications: number;
  recent_applications: Array<{
    id: string;
    job_id?: string | null;
    job_title: string;
    status: string;
    created_at?: string | null;
  }>;
  recent_referrals: Array<{
    id: string;
    candidate_name: string;
    job_id?: string | null;
    job_title?: string | null;
    status: string;
    bonus?: ApiBonusSummary | null;
    created_at?: string | null;
  }>;
}

export interface ManagerDashboardData {
  jobs_total: number;
  jobs_open: number;
  applications_total: number;
  applications_to_review: number;
  referrals_to_review: number;
  bonuses_to_approve: number;
  recent_applicants: Array<{
    id: string;
    job_id?: string | null;
    job_title: string;
    employee_id?: string | null;
    applicant?: ApiPersonRef | null;
    status: string;
    created_at?: string | null;
  }>;
  referral_queue: Array<{
    id: string;
    candidate_name: string;
    job_id?: string | null;
    job_title?: string | null;
    referrer_id?: string | null;
    referrer?: ApiPersonRef | null;
    status: string;
    bonus?: ApiBonusSummary | null;
    created_at?: string | null;
  }>;
}


export interface ApplicationsResponse {
  items: ApiApplication[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
}

export interface JobsResponse {
  items: ApiJob[];
  page: number;
  page_size: number;
  total: number;
}

export interface ApplicantRef {
  id: string;
  full_name: string | null;
  email: string | null;
  title?: string | null;
  team?: string | null;
  location?: string | null;
  has_resume?: boolean;
}


export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

const TOKEN_KEY = "talenthub_token";
const USER_KEY = "talenthub_user";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setSession(token: string | null, user: ApiUser | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  } catch {
    // Storage unavailable (private mode); API still works per-request.
  }
}

export function getStoredUser(): ApiUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as ApiUser) : null;
  } catch {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      const first = data.detail[0];
      if (typeof first?.msg === "string") return first.msg;
    }
    return `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

async function requestMultipart<T>(path: string, form: FormData): Promise<T> {
  // Do not set Content-Type manually; the browser adds the multipart boundary.
  const token = getToken();
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the TalentHub API. Check that the backend is running.");
  }
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return (await res.json()) as T;
}

async function downloadBlob(path: string): Promise<Blob> {
  const token = getToken();
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      credentials: "include",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch {
    throw new ApiError(0, "Cannot reach the TalentHub API. Check that the backend is running.");
  }
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return await res.blob();
}


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      // Send the HTTP-only access_token cookie alongside the bearer header.
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    // Network failure / backend unreachable: surface an explicit error rather
    // than letting the UI silently fall back to stale sample data.
    throw new ApiError(0, "Cannot reach the TalentHub API. Check that the backend is running.");
  }
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}


export const api = {
  register(payload: { full_name: string; email: string; password: string }) {
    return request<{ user: ApiUser }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  async login(payload: { email: string; password: string }) {
    const data = await request<{ access_token: string; token_type: string; user: ApiUser }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify(payload) }
    );
    setSession(data.access_token, data.user);
    return data;
  },
  fetchMe() {
    return request<{ user: ApiUser }>("/auth/me");
  },
  async logout() {
    try {
      await request<{ message: string }>("/auth/logout", { method: "POST" });
    } finally {
      setSession(null, null);
    }
  },
  listJobs(params: { q?: string; location?: string; page?: number; page_size?: number; sort?: string } = {}) {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.location) search.set("location", params.location);
    search.set("page", String(params.page ?? 1));
    search.set("page_size", String(params.page_size ?? 12));
    search.set("sort", params.sort ?? "newest");
    return request<JobsResponse>(`/jobs?${search.toString()}`);
  },
  getJob(jobId: string) {
    return request<{ job: ApiJob }>(`/jobs/${jobId}`);
  },
  applyToJob(jobId: string, payload: { cover_note?: string } = {}) {
    return request<{ application: ApiApplication }>(`/jobs/${jobId}/applications`, {
      method: "POST",
      body: JSON.stringify({ cover_note: payload.cover_note ?? "" }),
    });
  },
  myApplications(page = 1, pageSize = 20) {
    return request<ApplicationsResponse>(`/applications/me?page=${page}&page_size=${pageSize}`);
  },
  myApplicationForJob(jobId: string) {
    const search = new URLSearchParams({ job_id: jobId, page: "1", page_size: "1" });
    return request<ApplicationsResponse>(`/applications/me?${search.toString()}`);
  },
  getApplication(applicationId: string) {
    return request<{ application: ApiApplication }>(`/applications/${applicationId}`);
  },
  withdrawApplication(applicationId: string) {
    return request<{ message: string }>(`/applications/${applicationId}/withdraw`, { method: "POST" });
  },
  jobApplications(jobId: string, page = 1, pageSize = 20) {
    return request<ApplicationsResponse>(`/jobs/${jobId}/applications?page=${page}&page_size=${pageSize}`);
  },
  updateApplicationStatus(applicationId: string, payload: { status: string; reason?: string }) {
    return request<{ message: string }>(`/applications/${applicationId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  managedJobs(params: { q?: string; status?: string; page?: number; page_size?: number } = {}) {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.status) search.set("status", params.status);
    search.set("page", String(params.page ?? 1));
    search.set("page_size", String(params.page_size ?? 10));
    return request<ManagedJobsResponse>(`/jobs/managed?${search.toString()}`);
  },
  createJob(payload: JobCreatePayload) {
    return request<{ job: ApiJob }>("/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateJob(jobId: string, payload: JobUpdatePayload) {
    return request<{ job: ApiJob }>(`/jobs/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  updateJobStatus(jobId: string, status: JobStatus) {
    return request<{ job: ApiJob }>(`/jobs/${jobId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },
  deleteJob(jobId: string) {
    return request<{ message: string }>(`/jobs/${jobId}`, { method: "DELETE" });
  },
  getProfile() {
    return request<{ user: ApiProfile }>("/users/me");
  },
  updateProfile(payload: { full_name?: string; email?: string; phone?: string | null; title?: string | null; team?: string | null; location?: string | null; skills?: string[] }) {
    return request<{ user: ApiProfile }>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  changePassword(payload: { current_password: string; new_password: string; confirm_password: string }) {
    return request<{ message: string; user: ApiProfile }>("/users/me/change-password", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  uploadAvatar(file: globalThis.File) {
    const form = new FormData();
    form.append("file", file, file.name);
    return requestMultipart<{ user: ApiProfile }>("/users/me/avatar", form);
  },
  deleteAvatar() {
    return request<{ message: string }>("/users/me/avatar", { method: "DELETE" });
  },
  /** Cache-busted URL for a stored avatar so a replaced photo refreshes immediately. */
  avatarUrl(userId: string, uploadedAt?: string | null) {
    const stamp = uploadedAt ? `?v=${encodeURIComponent(uploadedAt)}` : "";
    return `${API_BASE_URL}/users/${userId}/avatar${stamp}`;
  },
  uploadResume(file: globalThis.File) {
    const form = new FormData();
    form.append("file", file, file.name);
    return requestMultipart<{ user: ApiProfile }>("/users/me/resume", form);
  },
  resumeMetadata() {
    return request<{ resume: ApiResume }>("/users/me/resume");
  },
  downloadOwnResume() {
    return downloadBlob("/users/me/resume/download");
  },
  deleteResume() {
    return request<{ message: string }>("/users/me/resume", { method: "DELETE" });
  },
  downloadApplicantResume(userId: string) {
    return downloadBlob(`/users/${userId}/resume/download`);
  },
  createReferral(payload: { candidate_name: string; candidate_email: string; job_id?: string | null; note?: string }) {
    return request<{ referral: ApiReferral }>("/referrals", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  myReferrals(params: { q?: string; status?: string; page?: number; page_size?: number } = {}) {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.status) search.set("status", params.status);
    search.set("page", String(params.page ?? 1));
    search.set("page_size", String(params.page_size ?? 10));
    return request<ReferralsResponse>(`/referrals/me?${search.toString()}`);
  },
  getReferral(referralId: string) {
    return request<{ referral: ApiReferral }>(`/referrals/${referralId}`);
  },
  allReferrals(params: { q?: string; status?: string; page?: number; page_size?: number } = {}) {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.status) search.set("status", params.status);
    search.set("page", String(params.page ?? 1));
    search.set("page_size", String(params.page_size ?? 10));
    return request<ReferralsResponse>(`/admin/referrals?${search.toString()}`);
  },
  updateReferralStatus(referralId: string, status: string, reason?: string) {
    return request<{ referral: ApiReferral }>(`/admin/referrals/${referralId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, reason }),
    });
  },
  allBonuses(params: { q?: string; approval_status?: string; page?: number; page_size?: number } = {}) {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.approval_status) search.set("approval_status", params.approval_status);
    search.set("page", String(params.page ?? 1));
    search.set("page_size", String(params.page_size ?? 10));
    return request<BonusesResponse>(`/admin/referral-bonuses?${search.toString()}`);
  },
  employeeDashboard() {
    return request<EmployeeDashboardData>("/dashboard/employee");
  },
  managerDashboard() {
    return request<ManagerDashboardData>("/dashboard/hiring-manager");
  },
};
