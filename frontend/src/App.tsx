import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { AuthProvider, initialsFor, roleLabel, useAuth, type UiRole } from "./context/AuthContext";
import {
  ApiError,
  api,
  type ApiApplication,
  type ApiAvatar,
  type ApiJob,
  type JobStatus,
  type ApiReferral,
  type ApiResume,
  type ApiUser,
} from "./services/api";

export type Role = UiRole;
type Screen =
  | "login"
  | "register"
  | "dashboard"
  | "jobs"
  | "job"
  | "refer"
  | "planner"
  | "applications"
  | "my-referrals"
  | "referral-detail"
  | "profile"
  | "post-job"
  | "manage-jobs"
  | "applicants"
  | "referrals"
  | "403"
  | "404";


const iconPaths: Record<string, ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  jobs: <><rect x="3" y="6" width="18" height="14" rx="2" /><path d="M8 6V4h8v2M3 11h18M10 11v2h4v-2" /></>,
  file: <><path d="M6 2h8l4 4v16H6zM14 2v5h5" /><path d="M9 12h6M9 16h6" /></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M20 8v6M23 11h-6" /><circle cx="8.5" cy="7" r="4" /></>,
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 22a8 8 0 0 1 16 0" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  moon: <path d="M20 15.3A8.5 8.5 0 0 1 8.7 4 8.7 8.7 0 1 0 20 15.3Z" />,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  pin: <><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  chevron: <path d="m9 18 6-6-6-6" />,
  check: <path d="m5 12 4 4L19 6" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  spark: <path d="m12 2 1.7 6.3L20 10l-6.3 1.7L12 18l-1.7-6.3L4 10l6.3-1.7L12 2Z" />,
  logout: <><path d="M10 17l5-5-5-5M15 12H3M15 4h5v16h-5" /></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  eye: <><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" /><circle cx="12" cy="12" r="2.5" /></>,
  trash: <><path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6" /></>,
  edit: <><path d="m4 20 4.5-1 10-10-3.5-3.5-10 10L4 20Z" /><path d="m13.5 7 3.5 3.5" /></>,
  gift: <><rect x="3" y="9" width="18" height="12" rx="2" /><path d="M12 9v12M3 13h18M7.5 9C5 9 4 5 6.5 4c2-.8 4 2 5.5 5M16.5 9C19 9 20 5 17.5 4c-2-.8-4 2-5.5 5" /></>,
};

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{iconPaths[name]}</svg>;
}

function Button({ children, variant = "primary", onClick, type = "button", disabled = false, className = "" }: { children: ReactNode; variant?: "primary" | "secondary" | "ghost" | "danger"; onClick?: () => void; type?: "button" | "submit"; disabled?: boolean; className?: string }) {
  return <button type={type} disabled={disabled} onClick={onClick} className={`btn btn-${variant} ${className}`}>{children}</button>;
}

function Brand({ compact = false }: { compact?: boolean }) {
  return <div className="brand"><span className="brand-mark">CL</span>{!compact && <span>CirrusLabs <strong>TalentHub</strong></span>}</div>;
}

function Field({ label, placeholder, type = "text", helper, error, defaultValue, value, onChange, disabled = false }: { label: string; placeholder?: string; type?: string; helper?: string; error?: string; defaultValue?: string; value?: string; onChange?: (v: string) => void; disabled?: boolean }) {
  const [visible, setVisible] = useState(false);
  return <label className={`field ${error ? "has-error" : ""}`}><span>{label}</span><div className="input-wrap"><input value={value ?? defaultValue ?? ""} onChange={onChange ? (e) => onChange(e.target.value) : undefined} type={type === "password" && visible ? "text" : type} placeholder={placeholder} disabled={disabled} />{type === "password" && <button type="button" className="input-action" onClick={() => setVisible(!visible)} aria-label="Show or hide password"><Icon name="eye" size={18} /></button>}</div>{error && <small className="error-text">{error}</small>}{helper && !error && <small>{helper}</small>}</label>;
}

function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

function Avatar({ initials = "?", src, alt = "" }: { initials?: string; src?: string | null; alt?: string }) {
  // An uploaded photo wins; otherwise show initials derived from the real name.
  if (src) {
    return (
      <span className="avatar">
        <img
          src={src}
          alt={alt}
          className="avatar-image"
          onError={(e) => {
            // If the stored photo can no longer be served, fall back to initials
            // instead of showing a broken image.
            e.currentTarget.style.display = "none";
          }}
        />
      </span>
    );
  }
  return <span className="avatar">{initials}</span>;
}

/** Builds the authenticated user's avatar source, if they have uploaded a photo. */
function useAvatarSrc(avatar?: ApiAvatar | null, userId?: string) {
  return useMemo(
    () => (avatar && userId ? api.avatarUrl(userId, avatar.uploaded_at) : null),
    [avatar, userId]
  );
}


function Auth({ register, onAuth }: { register: boolean; onAuth: () => void }) {
  const { login, register: signup } = useAuth();
  const [next, setNext] = useState(register);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const fieldError = (k: string) => errors[k];
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const nextErrors: Record<string, string> = {};
    if (register && fullName.trim().length < 2) nextErrors.full_name = "Enter your full name";
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) nextErrors.email = "Enter a valid work email";
    else if (register && !email.trim().toLowerCase().endsWith("@cirruslabs.io")) nextErrors.email = "Use your @cirruslabs.io work email";
    if (register && (password.length < 8 || !/[A-Za-z]/.test(password) || !/[0-9]/.test(password))) nextErrors.password = "Use 8+ characters with a letter and a number";
    else if (!register && !password) nextErrors.password = "Enter your password";
    if (register && confirm !== password) nextErrors.confirm = "Passwords do not match";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setBusy(true);
    try {
      if (register) await signup(fullName.trim(), email.trim(), password);
      else await login(email.trim(), password);
      onAuth();
    } catch (err) {
      setErrors({ form: err instanceof Error ? err.message : "Authentication failed" });
    } finally {
      setBusy(false);
    }
  };
  if (next !== register) return <Auth register={next} onAuth={onAuth} />;
  return <main className="auth">
    <section className="auth-hero">
      <Brand />
      <div className="hero-copy">
        <span className="hero-kicker">Grow from within</span>
        <h1>Discover opportunities within CirrusLabs.</h1>
        <p>Take the next step in your career, connect great people to great teams, and grow with us.</p>
        <div className="hero-points">
          {[["jobs", "Internal mobility", "Explore roles built for your next chapter."], ["users", "Employee referrals", "Bring remarkable people into CirrusLabs."], ["spark", "Hiring visibility", "Stay informed at every step of the journey."]].map(([icon, title, copy]) => <div key={title}><span><Icon name={icon} /></span><div><strong>{title}</strong><small>{copy}</small></div></div>)}
        </div>
      </div>
      <p className="auth-footer">CirrusLabs People & Culture · Private and confidential</p>
    </section>
    <section className="auth-form-side">
      <div className="auth-mobile-brand"><Brand /></div>
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-heading"><span className="eyebrow">{register ? "Join TalentHub" : "Welcome back"}</span><h2>{register ? "Create your account" : "Sign in to your account"}</h2><p>{register ? "Use your CirrusLabs work email to get started." : "Enter your work credentials to continue."}</p></div>
        {register && <Field label="Full name" placeholder="Your full name" value={fullName} onChange={setFullName} error={fieldError("full_name")} />}
        <Field label="Work email" type="email" placeholder="you@cirruslabs.io" value={email} onChange={setEmail} error={fieldError("email")} helper={register ? "Only @cirruslabs.io email addresses are accepted" : undefined} />
        <Field label="Password" type="password" placeholder={register ? "Create a secure password" : "Enter your password"} value={password} onChange={setPassword} error={fieldError("password")} helper={register ? "Minimum 8 characters with a letter and a number" : undefined} />
        {register && <Field label="Confirm password" type="password" placeholder="Enter your password again" value={confirm} onChange={setConfirm} error={fieldError("confirm")} />}
        {!register && <div className="role-choice"><span>Server workspace</span><div><span className="workspace-note">Your workspace is assigned by the server after sign-in.</span></div></div>}
        {errors.form && <p className="error-text" role="alert">{errors.form}</p>}
        <Button type="submit" className="full" disabled={busy}>{busy ? (register ? "Creating account…" : "Signing in…") : (<>{register ? "Create account" : "Sign in"} <Icon name="arrow" size={18} /></>)}</Button>
        <p className="auth-switch">{register ? "Already have an account?" : "New here?"} <button type="button" onClick={() => setNext(!register)}>{register ? "Sign in" : "Create an account"}</button></p>
      </form>
    </section>
  </main>;
}

const employeeNav: [string, string, Screen][] = [["dashboard", "Dashboard", "dashboard"], ["jobs", "Jobs", "jobs"], ["file", "My Applications", "applications"], ["users", "My Referrals", "my-referrals"], ["user", "Profile", "profile"]];
const managerNav: [string, string, Screen][] = [["dashboard", "Dashboard", "dashboard"], ["plus", "Post Job", "post-job"], ["jobs", "Manage Jobs", "manage-jobs"], ["users", "Referrals", "referrals"], ["user", "Profile", "profile"]];

function Sidebar({ account, role, screen, navigate, open, close, logout }: { account: ApiUser; role: Role; screen: Screen; navigate: (s: Screen) => void; open: boolean; close: () => void; logout: () => void }) {
  const items = role === "employee" ? employeeNav : managerNav;
  const photo = useAvatarSrc(account.avatar, account.id);
  return <><aside className={`sidebar ${open ? "open" : ""}`}><div className="side-brand"><Brand /><button className="mobile-close" onClick={close}><Icon name="close" /></button></div><div className="workspace-label">{role === "employee" ? "Employee workspace" : "Hiring manager workspace"}</div><nav>{items.map(([icon, label, target]) => <button key={label} className={screen === target ? "active" : ""} onClick={() => { navigate(target); close(); }}><Icon name={icon} /><span>{label}</span>{screen === target && <i />}</button>)}</nav><div className="side-bottom"><div className="side-user"><Avatar initials={initialsFor(account.full_name, account.email)} src={photo} alt={account.full_name} /><div><strong>{account.full_name}</strong><small>{roleLabel(account.role)}</small></div></div><button onClick={logout}><Icon name="logout" /><span>Log out</span></button></div></aside>{open && <button className="drawer-backdrop" onClick={close} aria-label="Close navigation" />}</>;
}


const pageMeta: Partial<Record<Screen, [string, string]>> = {
  dashboard: ["Dashboard", "Here’s what’s happening with your talent journey."],
  jobs: ["Explore jobs", "Find the next opportunity to grow your career at CirrusLabs."],
  job: ["Job details", "Review the role and see how your profile matches."],
  refer: ["Refer a colleague", "Help us connect with great talent."],
  planner: ["Interview planner", "Prepare with a plan tailored to this role."],
  applications: ["My applications", "Track your internal applications in one place."],
  "my-referrals": ["My referrals", "Follow your referrals and bonus eligibility."],
  "referral-detail": ["Referral details", "Review progress, dates, and bonus information."],
  profile: ["Profile", "Keep your details and skills up to date."],
  "post-job": ["Post a job", "Create a new opportunity for CirrusLabs talent."],
  "manage-jobs": ["Manage jobs", "Review and manage your open and closed roles."],
  applicants: ["Applicants", "Review candidates for Senior Product Designer."],
  referrals: ["Referrals", "Review employee referrals and manage outcomes."],
};

function Topbar({ screen, account, dark, setDark, menu }: { screen: Screen; account: ApiUser; dark: boolean; setDark: (v: boolean) => void; menu: () => void }) {
  const [title, subtitle] = pageMeta[screen] || ["TalentHub", "Move talent forward."];
  const photo = useAvatarSrc(account.avatar, account.id);
  return <header className="topbar"><button className="menu-button" onClick={menu} aria-label="Open navigation"><Icon name="menu" /></button><div><h1>{title}</h1><p>{subtitle}</p></div><div className="top-actions"><button className="icon-btn" onClick={() => setDark(!dark)} aria-label="Toggle theme"><Icon name={dark ? "sun" : "moon"} /></button><span className="top-divider" /><Avatar initials={initialsFor(account.full_name, account.email)} src={photo} alt={account.full_name} /><div className="top-user"><strong>{account.full_name}</strong><Pill tone="blue">{roleLabel(account.role)}</Pill></div></div></header>;
}


function StatCard({ icon, label, value, meta, tone = "blue", loading = false }: { icon: string; label: string; value: string | number; meta: string; tone?: string; loading?: boolean }) {
  // `meta` is derived from real counts by the caller. While a request is in
  // flight the value shows a dash instead of a fabricated number.
  return <article className="stat-card"><div className={`stat-icon ${tone}`}><Icon name={icon} /></div><div><p>{label}</p><strong>{loading ? "—" : value}</strong><small>{meta}</small></div></article>;
}

function Match({ value }: { value: number }) {
  return <div className="match"><span>{value}%</span><small>skill match</small></div>;
}

function JobCard({ job, navigate }: { job: { title: string; team: string; location: string; type?: string; experience?: string; match?: number; skills: string[]; id?: string }; navigate: (s: Screen, jobId?: string) => void }) {
  return <article className="job-card"><div className="job-head"><span className="company-mark">CL</span>{typeof job.match === "number" ? <Match value={job.match} /> : <span className="job-status-tag">Open</span>}</div><h3>{job.title}</h3><p className="company">{job.team}</p><div className="job-meta"><span><Icon name="pin" size={16} />{job.location}</span><span><Icon name="clock" size={16} />{job.type ?? "Full-time"}{job.experience ? ` · ${job.experience}` : ""}</span></div><div className="chips">{job.skills.map((skill) => <span key={skill}>{skill}</span>)}</div><div className="job-foot"><small>CirrusLabs TalentHub</small><Button variant="secondary" onClick={() => navigate("job", job.id)}>View role <Icon name="arrow" size={16} /></Button></div></article>;
}

/** Shared empty / error presentation so every data panel behaves consistently. */
function PanelState({ loading, error, empty, emptyTitle, emptyCopy }: { loading: boolean; error: string | null; empty: boolean; emptyTitle: string; emptyCopy: string }) {
  if (loading) return <section className="panel"><p>Loading…</p></section>;
  if (error) return <section className="panel"><p role="alert" className="error-text">{error}</p><p>Nothing is displayed because live data could not be loaded.</p></section>;
  if (empty) return <section className="panel"><h2>{emptyTitle}</h2><p>{emptyCopy}</p></section>;
  return null;
}

/** Relative "time ago" label derived from a real timestamp. */
function timeAgo(iso?: string | null): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const seconds = Math.max(1, Math.round((Date.now() - then) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d`;
  return formatDate(iso);
}

/** First name for a friendly greeting; never a hardcoded person. */
function firstName(fullName: string): string {
  return fullName.trim().split(/\s+/).filter(Boolean)[0] ?? fullName;
}


function EmployeeDashboard({ account, navigate }: { account: ApiUser; navigate: (s: Screen) => void }) {
  const [data, setData] = useState<EmployeeDashboardData | null>(null);
  const [jobs, setJobs] = useState<ApiJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([api.employeeDashboard(), api.listJobs({ page: 1, page_size: 2, sort: "newest" })])
      .then(([summary, jobPage]) => {
        if (cancelled) return;
        setData(summary);
        setJobs(jobPage.items);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setData(null);
        setJobs([]);
        setError(err instanceof Error ? err.message : "Could not load your dashboard");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => load(), [load]);

  return <>
    <section className="welcome"><div><span className="eyebrow">Your talent journey</span><h2>Good to see you, {firstName(account.full_name)}.</h2><p>{data ? `${data.open_jobs} internal ${data.open_jobs === 1 ? "role is" : "roles are"} open right now.` : "Loading your internal opportunities…"}</p></div><Button onClick={() => navigate("jobs")}>Explore opportunities <Icon name="arrow" size={17} /></Button></section>
    <div className="stats-grid">
      <StatCard icon="jobs" label="Open roles" value={data?.open_jobs ?? 0} meta="Open internal roles" loading={loading} />
      <StatCard icon="file" label="My applications" value={data?.applications_total ?? 0} meta={`${data?.applications_active ?? 0} still active`} tone="teal" loading={loading} />
      <StatCard icon="users" label="My referrals" value={data?.referrals_total ?? 0} meta={`${data?.referrals_pending ?? 0} awaiting review`} tone="purple" loading={loading} />
      <StatCard icon="spark" label="Unread updates" value={data?.unread_notifications ?? 0} meta="Notifications for you" tone="red" loading={loading} />
    </div>
    {error && <section className="panel"><p role="alert" className="error-text">{error}</p><Button variant="secondary" onClick={load}>Try again</Button></section>}
    <div className="content-grid">
      <section className="panel">
        <div className="panel-heading"><div><h2>Latest internal roles</h2><p>Newest open jobs</p></div><Button variant="ghost" onClick={() => navigate("jobs")}>View all <Icon name="arrow" size={16} /></Button></div>
        <div className="job-list">
          {loading && <p>Loading roles…</p>}
          {!loading && !error && jobs.length === 0 && <p>No internal roles are open right now.</p>}
          {jobs.map((job) => <JobCard key={job.id} job={toCardJob(job)} navigate={navigate} />)}
        </div>
      </section>
      <aside className="panel activity">
        <div className="panel-heading"><div><h2>Recent activity</h2><p>Your applications and referrals</p></div></div>
        {loading && <p style={{ padding: "0 18px" }}>Loading activity…</p>}
        {!loading && data && data.recent_applications.length === 0 && data.recent_referrals.length === 0 && <p style={{ padding: "0 18px" }}>No applications or referrals yet.</p>}
        {data?.recent_applications.map((app) => <div className="activity-item" key={`app-${app.id}`}><span><Icon name="file" size={17} /></span><div><strong>Applied · {app.status.replace(/_/g, " ")}</strong><p>{app.job_title}</p></div><small>{timeAgo(app.created_at)}</small></div>)}
        {data?.recent_referrals.map((ref) => <div className="activity-item" key={`ref-${ref.id}`}><span><Icon name="users" size={17} /></span><div><strong>Referral · {ref.status}</strong><p>{ref.candidate_name}{ref.job_title ? ` · ${ref.job_title}` : ""}</p></div><small>{timeAgo(ref.created_at)}</small></div>)}
      </aside>
    </div>
  </>;
}


function ManagerDashboard({ account, navigate }: { account: ApiUser; navigate: (s: Screen) => void }) {
  const [data, setData] = useState<ManagerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.managerDashboard()
      .then((summary) => { if (!cancelled) setData(summary); })
      .catch((err: unknown) => {
        if (cancelled) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Could not load your hiring dashboard");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => load(), [load]);

  return <>
    <section className="welcome manager-welcome"><div><span className="eyebrow">Hiring overview</span><h2>Welcome back, {firstName(account.full_name)}.</h2><p>{data ? `${data.jobs_open} open ${data.jobs_open === 1 ? "requisition" : "requisitions"} · ${data.referrals_to_review} ${data.referrals_to_review === 1 ? "referral" : "referrals"} awaiting review.` : "Loading your hiring pipeline…"}</p></div><Button onClick={() => navigate("post-job")}><Icon name="plus" size={17} /> Post a job</Button></section>
    <div className="stats-grid">
      <StatCard icon="jobs" label="Open jobs" value={data?.jobs_open ?? 0} meta={`${data?.jobs_total ?? 0} total requisitions`} loading={loading} />
      <StatCard icon="file" label="Total applicants" value={data?.applications_total ?? 0} meta={`${data?.applications_to_review ?? 0} to review`} tone="teal" loading={loading} />
      <StatCard icon="users" label="Referrals to review" value={data?.referrals_to_review ?? 0} meta={data && data.referrals_to_review > 0 ? "Needs attention" : "All reviewed"} tone="purple" loading={loading} />
      <StatCard icon="gift" label="Bonuses to approve" value={data?.bonuses_to_approve ?? 0} meta={data && data.bonuses_to_approve > 0 ? "Awaiting decision" : "Nothing pending"} tone="red" loading={loading} />
    </div>
    {error && <section className="panel"><p role="alert" className="error-text">{error}</p><Button variant="secondary" onClick={load}>Try again</Button></section>}
    <div className="content-grid">
      <section className="panel">
        <div className="panel-heading"><div><h2>Recent applicants</h2><p>Latest applications on your roles</p></div><Button variant="ghost" onClick={() => navigate("applicants")}>View all <Icon name="arrow" size={16} /></Button></div>
        <div className="people-list">
          {loading && <p>Loading applicants…</p>}
          {!loading && !error && (data?.recent_applicants.length ?? 0) === 0 && <p>No applications have been received yet.</p>}
          {data?.recent_applicants.map((app) => <div key={app.id}>
            <Avatar initials={initialsFor(app.applicant?.full_name, app.applicant?.email)} />
            <div><strong>{app.applicant?.full_name ?? "Unknown applicant"}</strong><p>{app.job_title} · {formatDate(app.created_at)}</p></div>
            <Pill tone={statusTone(app.status)}>{app.status.replace(/_/g, " ")}</Pill>
            <Button variant="secondary" onClick={() => navigate("applicants")}>Review</Button>
          </div>)}
        </div>
      </section>
      <aside className="panel activity">
        <div className="panel-heading"><div><h2>Referral queue</h2><p>{data ? `${data.referrals_to_review} ${data.referrals_to_review === 1 ? "referral" : "referrals"} need review` : "Loading referrals…"}</p></div></div>
        {loading && <p style={{ padding: "0 18px" }}>Loading referrals…</p>}
        {!loading && !error && (data?.referral_queue.length ?? 0) === 0 && <p style={{ padding: "0 18px" }}>No referrals have been submitted yet.</p>}
        {data?.referral_queue.map((ref) => <div className="activity-item" key={ref.id}>
          <Avatar initials={initialsFor(ref.candidate_name)} />
          <div><strong>{ref.candidate_name}</strong><p>{ref.job_title ?? "General referral"} · {ref.status}{ref.referrer?.full_name ? ` · referred by ${ref.referrer.full_name}` : ""}</p></div>
          <small>{timeAgo(ref.created_at)}</small>
        </div>)}
        <Button variant="secondary" className="full" onClick={() => navigate("referrals")}>Review referrals</Button>
      </aside>
    </div>
  </>;
}

function toCardJob(job: ApiJob) {
  return {
    id: job.id,
    title: job.title,
    team: job.team,
    location: job.location,
    type: job.employment_type ?? "Full-time",
    experience: job.experience ?? "",
    // No match percentage is invented: the project stores no ATS score, so the
    // card renders the real publication state instead of a fabricated number.
    match: undefined as number | undefined,
    skills: job.skills ?? [],
  };
}

function Jobs({ navigate }: { navigate: (s: Screen, jobId?: string) => void }) {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<ApiJob[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 12;

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listJobs({ q: query || undefined, location: location || undefined, page, page_size: pageSize, sort });
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not load jobs");
        // Preserve existing demo content as fallback; API remains primary.
        setItems([]);
        setTotal(0);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    const timer = setTimeout(load, query ? 350 : 0);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query, location, sort, page]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return <><div className="toolbar"><div className="search-box"><Icon name="search" /><input aria-label="Search jobs" placeholder="Search by role, skill, or team" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} /></div><select aria-label="Location" value={location} onChange={(e) => { setLocation(e.target.value); setPage(1); }}><option value="">All locations</option><option>Bengaluru</option><option>Pune</option><option>Remote</option></select><select aria-label="Job type"><option>All job types</option><option>Full-time</option></select></div><div className="results-row"><p><strong>{loading ? "Loading…" : `${total} ${total === 1 ? "opportunity" : "opportunities"}`}</strong> open right now</p><select aria-label="Sort jobs" value={sort} onChange={(e) => { setSort(e.target.value === "Most recent" ? "newest" : "newest"); setPage(1); }}><option>Best match</option><option>Most recent</option></select></div>{loading && <section className="panel"><p>Loading internal jobs…</p></section>}{!loading && error && <section className="panel"><p role="alert" className="error-text">{error}</p><p>Open roles are unavailable until the API is reachable.</p><Button variant="secondary" onClick={() => setPage((p) => p)}>Reload</Button></section>}{!loading && !error && total === 0 && <section className="panel"><h2>No open roles found</h2><p>{query || location ? "Try a different search or clear your filters." : "Check back later — no jobs are open right now."}</p></section>}<div className="jobs-grid">{items.map((job, i) => <JobCard key={job.id ?? i} job={toCardJob(job)} navigate={navigate} />)}</div><div className="pagination"><button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Previous</button><button className="active">{page}</button><span>of {totalPages}</span><button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</button></div></>;
}

/** Job detail — loads a real requisition and submits a real application. */
function JobDetailApi({ navigate, jobId }: { navigate: (s: Screen, jobId?: string) => void; jobId: string }) {
  const { user, logout } = useAuth();
  const [job, setJob] = useState<ApiJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coverNote, setCoverNote] = useState("");
  const [applyBusy, setApplyBusy] = useState(false);
  const [checkingApplication, setCheckingApplication] = useState(true);
  const [applicationLookupError, setApplicationLookupError] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [application, setApplication] = useState<ApiApplication | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setApplication(null);
    setApplyError(null);
    api.getJob(jobId).then((res) => {
      if (cancelled) return;
      setJob(res.job);
      setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      setError(err instanceof Error ? err.message : "Could not load this job");
      setLoading(false);
    });
    if (user?.role === "employee") {
      setCheckingApplication(true);
      setApplicationLookupError(null);
      api.myApplicationForJob(jobId).then((res) => {
        if (cancelled) return;
        setApplication(res.items[0] ?? null);
      }).catch((err) => {
        if (cancelled) return;
        setApplicationLookupError(err instanceof Error ? err.message : "Could not check your application status");
      }).finally(() => {
        if (!cancelled) setCheckingApplication(false);
      });
    } else {
      setCheckingApplication(false);
    }
    return () => { cancelled = true; };
  }, [jobId, user?.id, user?.role]);

  const applyForJob = async () => {
    if (applyBusy || application || !job || job.status !== "open" || user?.role !== "employee") return;
    if (coverNote.length > 5000) {
      setApplyError("Cover note must be 5000 characters or fewer");
      return;
    }
    setApplyBusy(true);
    setApplyError(null);
    try {
      const res = await api.applyToJob(jobId, { cover_note: coverNote.trim() });
      setApplication(res.application);
      setApplicationLookupError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const latest = await api.myApplicationForJob(jobId).catch(() => null);
        if (latest?.items[0]) {
          setApplication(latest.items[0]);
          setApplicationLookupError(null);
          setApplyError(null);
          return;
        }
      }
      setApplyError(err instanceof ApiError && err.status === 401
        ? "Your session expired. Please sign in again."
        : err instanceof Error ? err.message : "Application failed");
      if (err instanceof ApiError && err.status === 401) await logout();
    } finally {
      setApplyBusy(false);
    }
  };

  const submitApplication = (e: FormEvent) => {
    e.preventDefault();
    void applyForJob();
  };
  const applyLabel = application
    ? "Applied"
    : applyBusy
      ? "Applying…"
      : checkingApplication
        ? "Checking application…"
        : job?.status === "closed"
          ? "Job Closed"
          : user?.role === "employee"
            ? "Apply for this Role"
            : "Employees Only";
  const applicationButtonDisabled = applyBusy || checkingApplication || Boolean(application) ||
    job?.status !== "open" || user?.role !== "employee";

  if (loading) return <><button className="back-link" onClick={() => navigate("jobs")}>Back to jobs</button><section className="panel"><p>Loading job details…</p></section></>;
  if (error || !job) return <><button className="back-link" onClick={() => navigate("jobs")}>Back to jobs</button><section className="panel"><h2>Job unavailable</h2><p role="alert" className="error-text">{error ?? "This job is no longer available."}</p><p>It may have been closed or removed.</p></section></>;
  return <><button className="back-link" onClick={() => navigate("jobs")}>Back to jobs</button><section className="job-detail-head"><div><div className="title-row"><span className="company-mark large">CL</span><div><Pill tone="blue">{job.team}</Pill><h2>{job.title}</h2><p>CirrusLabs · {job.location}</p></div></div><div className="detail-tags"><span>{job.employment_type ?? "Full-time"}</span>{job.experience ? <span>{job.experience}</span> : null}{job.salary_band ? <span>{job.salary_band}</span> : null}<span>{job.status === "open" ? "Open for applications" : "Closed"}</span></div></div><div className="detail-actions"><Button disabled={applicationButtonDisabled} onClick={() => void applyForJob()}>{application ? <Icon name="check" /> : null}{applyLabel}</Button><Button variant="secondary" onClick={() => navigate("refer")}>Refer a colleague</Button></div></section>{applicationLookupError && <section className="panel"><p role="alert" className="error-text">Could not verify whether you have already applied: {applicationLookupError}</p></section>}{applyError && <section className="panel"><p role="alert" className="error-text">{applyError}</p></section>}<section className="panel"><form onSubmit={submitApplication}><Field label="Cover note (optional)" placeholder="Why are you a strong fit? (max 5000 characters)" value={coverNote} onChange={setCoverNote} helper="Visible only to the hiring team" /><Button type="submit" disabled={applicationButtonDisabled}>{applyLabel}</Button></form></section><div className="detail-layout"><article className="panel prose"><h2>About the role</h2><p>{job.description ?? "Internal opportunity posted on TalentHub."}</p><h2>Required skills</h2><div className="chips large-chips">{(job.skills?.length ? job.skills : ["General"]).map(x => <span key={x}>{x}</span>)}</div></article></div></>;
}

/** Tag/chip input used for skills. Value is controlled by the parent. */
function TagInput({ label, values, onChange, placeholder }: { label: string; values: string[]; onChange: (v: string[]) => void; placeholder: string }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const next = draft.trim();
    if (!next) return;
    if (!values.some((v) => v.toLowerCase() === next.toLowerCase())) onChange([...values, next]);
    setDraft("");
  };
  return <label className="field"><span>{label}</span>
    <div className="tag-input">
      {values.map((tag) => <span key={tag}>{tag} <button type="button" aria-label={`Remove ${tag}`} onClick={() => onChange(values.filter((v) => v !== tag))}>×</button></span>)}
      <input
        value={draft}
        placeholder={placeholder}
        aria-label={label}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={add}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); add(); } }}
      />
    </div>
    <small>Press Enter to add a skill.</small>
  </label>;
}

const EMPLOYMENT_TYPES = ["Full-time", "Contract", "Internship"];

/** Post a job — a real create form that persists through POST /jobs. */
function PostJobForm({ navigate }: { navigate: (s: Screen) => void }) {
  const [form, setForm] = useState({
    title: "", team: "", location: "", employment_type: "Full-time",
    salary_band: "", experience: "", description: "",
  });
  const [skills, setSkills] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (key: keyof typeof form) => (value: string) => setForm((prev) => ({ ...prev, [key]: value }));

  const validate = () => {
    const next: Record<string, string> = {};
    if (form.title.trim().length < 3) next.title = "Enter a job title (3+ characters)";
    if (form.team.trim().length < 2) next.team = "Enter the team or function";
    if (form.location.trim().length < 2) next.location = "Enter a location or Remote";
    if (form.description.trim().length < 20) next.description = "Describe the role in at least 20 characters";
    if (skills.length === 0) next.skills = "Add at least one required skill";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    if (!validate()) return;
    setBusy(true);
    setFormError(null);
    try {
      await api.createJob({
        title: form.title.trim(),
        team: form.team.trim(),
        location: form.location.trim(),
        employment_type: form.employment_type,
        experience: form.experience.trim(),
        salary_band: form.salary_band.trim(),
        description: form.description.trim(),
        skills,
      });
      navigate("manage-jobs");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not create the job");
    } finally {
      setBusy(false);
    }
  };

  return <form className="form-layout" onSubmit={submit}>
    <section className="panel form-card">
      <div className="form-section-head"><h2>New job</h2><p>New jobs are open to employees as soon as they are created.</p></div>
      {formError && <p role="alert" className="error-text">{formError}</p>}
      <Field label="Job title" placeholder="e.g. Senior Product Designer" value={form.title} onChange={set("title")} error={errors.title} />
      <div className="two-cols">
        <Field label="Team" placeholder="e.g. Product" value={form.team} onChange={set("team")} error={errors.team} />
        <Field label="Location" placeholder="City or Remote" value={form.location} onChange={set("location")} error={errors.location} />
      </div>
      <div className="three-cols">
        <label className="field"><span>Employment type</span>
          <select value={form.employment_type} onChange={(e) => set("employment_type")(e.target.value)}>
            {EMPLOYMENT_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </label>
        <Field label="Salary band" placeholder="e.g. ₹28L–₹36L" value={form.salary_band} onChange={set("salary_band")} />
        <Field label="Experience" placeholder="e.g. 5–8 years" value={form.experience} onChange={set("experience")} />
      </div>
      <label className={`field ${errors.description ? "has-error" : ""}`}><span>Job description</span>
        <textarea rows={7} placeholder="Describe the role, responsibilities, and impact…" value={form.description} onChange={(e) => set("description")(e.target.value)} />
        {errors.description && <small className="error-text">{errors.description}</small>}
      </label>
      <TagInput label="Required skills" values={skills} onChange={setSkills} placeholder="Add a skill" />
      {errors.skills && <p role="alert" className="error-text">{errors.skills}</p>}
      <div className="form-actions">
        <Button type="submit" disabled={busy}>{busy ? "Creating…" : "Create job"}</Button>
        <Button variant="ghost" onClick={() => navigate("manage-jobs")}>Cancel</Button>
      </div>
    </section>
    <aside className="panel summary-card">
      <span className="company-mark">CL</span>
      <h3>Job details checklist</h3>
      <ul>
        <li><Icon name={form.title.trim().length >= 3 ? "check" : "clock"} size={16} /> Clear, inclusive title</li>
        <li><Icon name={form.salary_band.trim() ? "check" : "clock"} size={16} /> Salary band included</li>
        <li><Icon name={skills.length > 0 ? "check" : "clock"} size={16} /> Relevant skills added</li>
        <li><Icon name={form.description.trim().length >= 20 ? "check" : "clock"} size={16} /> Full role description</li>
      </ul>
      <p>Jobs are open as soon as they are created. Close and reopen them from Manage Jobs.</p>
    </aside>
  </form>;
}

/** Refer a colleague — persists through POST /referrals. */
function ReferForm({ navigate, prefillJobId }: { navigate: (s: Screen, jobId?: string) => void; prefillJobId?: string }) {
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [note, setNote] = useState("");
  const [jobId, setJobId] = useState<string>(prefillJobId ?? "");
  const [openJobs, setOpenJobs] = useState<ApiJob[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.listJobs({ page: 1, page_size: 50, sort: "newest" })
      .then((res) => { if (!cancelled) setOpenJobs(res.items); })
      .catch(() => { if (!cancelled) setOpenJobs([]); });
    return () => { cancelled = true; };
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const next: Record<string, string> = {};
    if (candidateName.trim().length < 2) next.candidate_name = "Enter the candidate's full name";
    if (!/^\S+@\S+\.\S+$/.test(candidateEmail.trim())) next.candidate_email = "Enter a valid email address";
    setErrors(next);
    if (Object.keys(next).length) return;
    setBusy(true);
    setFormError(null);
    try {
      await api.createReferral({
        candidate_name: candidateName.trim(),
        candidate_email: candidateEmail.trim(),
        job_id: jobId || null,
        note: note.trim(),
      });
      setDone(candidateName.trim());
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not submit the referral");
    } finally {
      setBusy(false);
    }
  };

  if (done) return <div className="success-state"><span><Icon name="check" size={32} /></span><h2>Referral submitted</h2><p>{done} is now in the hiring pipeline. Track progress from My Referrals.</p><Button onClick={() => navigate("my-referrals")}>View my referrals</Button></div>;

  return <form className="form-layout" onSubmit={submit}>
    <section className="panel form-card">
      <div className="form-section-head"><h2>Refer a colleague</h2><p>We'll only use these details for this referral.</p></div>
      {formError && <p role="alert" className="error-text">{formError}</p>}
      <div className="two-cols">
        <Field label="Colleague name" placeholder="Full name" value={candidateName} onChange={setCandidateName} error={errors.candidate_name} />
        <Field label="Candidate email" placeholder="name@example.com" helper="Where we can reach them" value={candidateEmail} onChange={setCandidateEmail} error={errors.candidate_email} />
      </div>
      <label className="field"><span>Role</span>
        <select value={jobId} onChange={(e) => setJobId(e.target.value)}>
          <option value="">General referral (no specific role)</option>
          {openJobs.map((job) => <option key={job.id} value={job.id}>{job.title} · {job.location}</option>)}
        </select>
        <small>Only open roles can be referred against.</small>
      </label>
      <label className="field"><span>Why are they a great fit? <small>Optional</small></span>
        <textarea rows={5} placeholder="Share relevant context, skills, or experience…" value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      <div className="form-actions">
        <Button type="submit" disabled={busy}>{busy ? "Submitting…" : "Submit referral"}</Button>
        <Button variant="ghost" onClick={() => navigate("jobs")}>Cancel</Button>
      </div>
    </section>
    <aside className="panel summary-card">
      <span className="company-mark">CL</span>
      <h3>How referrals work</h3>
      <p>The hiring team reviews every referral. Bonus eligibility is decided separately by People &amp; Culture — a referral on its own does not guarantee a bonus.</p>
    </aside>
  </form>;
}

const AVATAR_ACCEPT = "image/jpeg,image/png,image/webp";
const AVATAR_MAX_BYTES = 2 * 1024 * 1024;

/** Change photo — validates, uploads to the backend, and persists across reloads. */
function PhotoCard({ profile, onSaved }: { profile: ApiProfile; onSaved: (p: ApiProfile) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const photo = useAvatarSrc(profile.avatar, profile.id);

  const pick = async (file: globalThis.File | null | undefined) => {
    if (!file) return;
    setError(null);
    setNotice(null);
    // Client-side checks mirror the server rules so failures are fast and clear.
    if (!AVATAR_ACCEPT.includes(file.type)) {
      setError("Choose a JPEG, PNG or WebP image.");
      return;
    }
    if (file.size > AVATAR_MAX_BYTES) {
      setError("Images must be 2 MB or smaller.");
      return;
    }
    setBusy(true);
    try {
      const res = await api.uploadAvatar(file);
      onSaved(res.user);
      setNotice("Profile photo updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await api.deleteAvatar();
      onSaved({ ...profile, avatar: null });
      setNotice("Profile photo removed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove the photo");
    } finally {
      setBusy(false);
    }
  };

  return <section className="panel form-card">
    <div className="form-section-head"><h2>Profile photo</h2><p>JPEG, PNG or WebP up to 2 MB. Stored on the server so it persists across sessions.</p></div>
    <div className="profile-intro">
      <Avatar initials={initialsFor(profile.full_name, profile.email)} src={photo} alt={profile.full_name} />
      <div><strong>{profile.full_name}</strong><p>{roleLabel(profile.role)}{profile.title ? ` · ${profile.title}` : ""}</p></div>
      <label className="btn btn-secondary photo-picker">
        {busy ? "Uploading…" : "Change photo"}
        <input type="file" accept={AVATAR_ACCEPT} disabled={busy} onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; void pick(f); }} />
      </label>
    </div>
    {profile.avatar && <div className="form-actions"><Button variant="ghost" disabled={busy} onClick={() => void remove()}>Remove photo</Button></div>}
    {error && <p role="alert" className="error-text">{error}</p>}
    {notice && <div className="inline-success"><Icon name="check" size={17} /> {notice}</div>}
  </section>;
}

/** Change password — verifies the current password server-side before updating. */
function PasswordCard() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const nextErrors: Record<string, string> = {};
    if (!current) nextErrors.current = "Enter your current password";
    if (next.length < 8 || !/[A-Za-z]/.test(next) || !/[0-9]/.test(next)) nextErrors.next = "Use 8+ characters with a letter and a number";
    if (confirm !== next) nextErrors.confirm = "Passwords do not match";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setBusy(true);
    setFormError(null);
    setNotice(null);
    try {
      await api.changePassword({ current_password: current, new_password: next, confirm_password: confirm });
      setNotice("Password updated. Use your new password next time you sign in.");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not change the password");
    } finally {
      setBusy(false);
    }
  };

  return <section className="panel form-card password-card">
    <div className="form-section-head"><h2>Change password</h2><p>Choose a strong password you don't use elsewhere. Changing it signs out your other sessions.</p></div>
    <form onSubmit={submit}>
      {formError && <p role="alert" className="error-text">{formError}</p>}
      <Field label="Current password" type="password" value={current} onChange={setCurrent} error={errors.current} />
      <Field label="New password" type="password" helper="Minimum 8 characters with a letter and a number" value={next} onChange={setNext} error={errors.next} />
      <Field label="Confirm new password" type="password" value={confirm} onChange={setConfirm} error={errors.confirm} />
      <Button type="submit" disabled={busy}>{busy ? "Updating…" : "Update password"}</Button>
      {notice && <div className="inline-success"><Icon name="check" size={17} /> {notice}</div>}
    </form>
  </section>;
}

/** Profile — loads, edits and persists the authenticated user's own record. */
function ProfilePage({ account, onSaved }: { account: ApiUser; onSaved: (u: ApiUser) => void }) {
  const [profile, setProfile] = useState<ApiProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [form, setForm] = useState({ full_name: "", phone: "", title: "", team: "", location: "" });
  const [skills, setSkills] = useState<string[]>([]);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.getProfile()
      .then((res) => {
        if (cancelled) return;
        setProfile(res.user);
        setForm({
          full_name: res.user.full_name ?? "",
          phone: res.user.phone ?? "",
          title: res.user.title ?? "",
          team: res.user.team ?? "",
          location: res.user.location ?? "",
        });
        setSkills(res.user.skills ?? []);
      })
      .catch((err: unknown) => { if (!cancelled) setError(err instanceof Error ? err.message : "Could not load your profile"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => load(), [load]);

  // Merge a freshly-saved profile into shared session state so the header,
  // sidebar and Profile page always agree without a reload.
  const persist = (next: ApiProfile) => {
    setProfile(next);
    onSaved(next);
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || !profile) return;
    if (form.full_name.trim().length < 2) {
      setFormError("Enter your full name (2+ characters)");
      return;
    }
    setBusy(true);
    setFormError(null);
    setNotice(null);
    try {
      const res = await api.updateProfile({
        full_name: form.full_name.trim(),
        phone: form.phone.trim() || null,
        title: form.title.trim() || null,
        team: form.team.trim() || null,
        location: form.location.trim() || null,
        skills,
      });
      persist(res.user);
      setNotice("Profile saved.");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not save your profile");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <PanelState loading error={null} empty={false} emptyTitle="" emptyCopy="" />;
  if (error || !profile) return <section className="panel"><h2>Profile unavailable</h2><p role="alert" className="error-text">{error ?? "Your profile could not be loaded."}</p><Button variant="secondary" onClick={load}>Try again</Button></section>;

  const isEmployee = profile.role === "employee";

  return <div className="form-layout profile-layout">
    <div>
      <form className="panel form-card" onSubmit={save} style={{ marginBottom: 20 }}>
        <div className="form-section-head"><h2>Your details</h2><p>This information is visible to the People team. Your role is assigned by the server and cannot be changed here.</p></div>
        {formError && <p role="alert" className="error-text">{formError}</p>}
        <div className="two-cols">
          <Field label="Full name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} />
          <Field label="Work email" value={profile.email} disabled helper="Contact People & Culture to change your work email" />
        </div>
        <div className="two-cols">
          <Field label="Phone" placeholder="+91 98765 43210" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
          <Field label="Location" placeholder="City or Remote" value={form.location} onChange={(v) => setForm({ ...form, location: v })} />
        </div>
        <div className="two-cols">
          <Field label="Job title" placeholder="e.g. Hiring Manager" value={form.title} onChange={(v) => setForm({ ...form, title: v })} />
          <Field label="Team" placeholder="e.g. People & Culture" value={form.team} onChange={(v) => setForm({ ...form, team: v })} />
        </div>
        {isEmployee && <TagInput label="Skills" values={skills} onChange={setSkills} placeholder="Add a skill" />}
        <div className="role-readonly"><span>Role</span><strong>{roleLabel(profile.role)}</strong><small>Assigned by the server. Editing a profile can never change your permissions.</small></div>
        <div className="form-actions"><Button type="submit" disabled={busy}>{busy ? "Saving…" : "Save changes"}</Button></div>
        {notice && <div className="inline-success"><Icon name="check" size={17} /> {notice}</div>}
      </form>
      <PasswordCard />
      {isEmployee && <ResumeCard />}
    </div>
    <div>
      <PhotoCard profile={profile} onSaved={persist} />
      <aside className="panel summary-card" style={{ marginTop: 20 }}>
        <span className="company-mark">CL</span>
        <h3>Account</h3>
        <p>Member since {formatDate(profile.created_at)}.</p>
        <p>Signed in as {roleLabel(profile.role)}.</p>
      </aside>
    </div>
  </div>;
}

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function statusTone(status: string): string {
  const s = status.toLowerCase();
  if (s.includes("reject") || s === "withdrawn") return "red";
  if (s === "shortlisted" || s === "hired" || s === "offered") return "teal";
  if (s === "interview") return "blue";
  return "amber";
}

const NEXT_STATUSES: Record<string, string[]> = {
  submitted: ["under_review", "shortlisted", "rejected"],
  under_review: ["shortlisted", "interview", "offered", "rejected"],
  shortlisted: ["interview", "offered", "rejected"],
  interview: ["offered", "hired", "rejected"],
  offered: ["hired", "rejected"],
};

function ApplicantsPanel({ jobId, navigate }: { jobId?: string; navigate: (s: Screen) => void }) {
  const [jobs, setJobs] = useState<ApiJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>(jobId ?? "");
  const [items, setItems] = useState<ApiApplication[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.managedJobs().then((res) => { if (!cancelled) setJobs(res.items); })
      .catch(() => { if (!cancelled) setJobs([]); });
    return () => { cancelled = true; };
  }, []);
  useEffect(() => {
    if (!jobId && !selectedJob && jobs.length) setSelectedJob(jobs[0].id);
  }, [jobId, selectedJob, jobs]);

  useEffect(() => {
    if (!selectedJob) { setLoading(false); setItems([]); setTotal(0); return; }
    let cancelled = false;
    setLoading(true); setError(null); setNotice(null);
    api.jobApplications(selectedJob, 1, 50).then((res) => {
      if (cancelled) return;
      setItems(res.items); setTotal(res.total); setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      setError(err instanceof Error ? err.message : "Could not load applicants"); setLoading(false);
    });
    return () => { cancelled = true; };
  }, [selectedJob]);

  const downloadResume = async (employeeId: string) => {
    setBusyId(employeeId); setNotice(null); setError(null);
    try {
      const blob = await api.downloadApplicantResume(employeeId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "resume.pdf";
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resume download failed");
    } finally { setBusyId(null); }
  };

  const updateStatus = async (app: ApiApplication, next: string) => {
    setBusyId(app.id); setError(null); setNotice(null);
    try {
      await api.updateApplicationStatus(app.id, { status: next });
      setItems((prev) => prev.map((x) => (x.id === app.id ? { ...x, status: next } : x)));
      setNotice(`${app.job_title}: status updated to ${next.replace("_", " ")}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update status");
    } finally { setBusyId(null); }
  };

  return <section className="panel table-panel">
    <div className="table-toolbar">
      <div className="search-box"><Icon name="search" /><input placeholder="Search" aria-label="Search applicants" /></div>
      {jobs.length > 0 && <label className="field" style={{ marginBottom: 0 }}><span className="visually-hidden">Job</span>
        <select aria-label="Select job" value={selectedJob} onChange={(e) => setSelectedJob(e.target.value)}>
          {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
        </select>
      </label>}
    </div>
    {loading && <p>Loading applicants…</p>}
    {error && <p role="alert" className="error-text">{error}</p>}
    {notice && <div className="inline-success"><Icon name="check" size={17} /> {notice}</div>}
    {!loading && !error && !selectedJob && <p>Select a job you manage to review its applicants.</p>}
    {!loading && selectedJob && items.length === 0 && <p>No applications yet for this job.</p>}
    {items.length > 0 && <div className="data-table">
      <div className="table-row table-head"><span>Applicant</span><span>Applied on</span><span>Status</span><span>Resume</span><span>Update status</span></div>
      {items.map((app) => <div className="table-row" key={app.id}>
        <span><strong>{app.applicant?.full_name ?? "Unknown applicant"}</strong>{app.applicant?.title && <small style={{ display: "block", color: "var(--muted)" }}>{app.applicant.title}</small>}</span>
        <span>{formatDate(app.created_at)}</span>
        <span><Pill tone={statusTone(app.status)}>{app.status.replace("_", " ")}</Pill></span>
        <span><Button variant="ghost" disabled={busyId === app.employee_id} onClick={() => void downloadResume(app.employee_id)}><Icon name="file" size={15} /> Resume</Button></span>
        <span>{NEXT_STATUSES[app.status] ? <label className="field" style={{ marginBottom: 0 }}><span className="visually-hidden">Status</span>
          <select aria-label={`Update status for ${app.job_title}`} value="" disabled={busyId === app.id} onChange={(e) => { if (e.target.value) void updateStatus(app, e.target.value); }}>
            <option value="">Change status…</option>
            {NEXT_STATUSES[app.status].map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </select></label> : <span>—</span>}</span>
      </div>)}
    </div>}
    <div className="table-footer"><p>Showing {items.length ? `1–${items.length}` : "0"} of {total}</p></div>
  </section>;
}

function ResumeCard() {
  const [resume, setResume] = useState<ApiResume | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    api.getProfile().then((res) => { if (!cancelled) setResume(res.user.resume ?? null); })
      .catch(() => { if (!cancelled) setResume(null); });
    return () => { cancelled = true; };
  }, []);
  const handleFile = async (file: globalThis.File | null | undefined) => {
    if (!file) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      const res = await api.uploadResume(file);
      setResume(res.user.resume ?? null);
      setNotice(res.user.resume ? `Resume ${res.user.resume.filename} uploaded.` : "Resume uploaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally { setBusy(false); }
  };
  const download = async () => {
    setBusy(true); setError(null); setNotice(null);
    try {
      const blob = await api.downloadOwnResume();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = resume?.filename ?? "resume.pdf";
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true); setError(null); setNotice(null);
    try {
      await api.deleteResume();
      setResume(null);
      setNotice("Resume removed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove resume");
    } finally { setBusy(false); }
  };
  return <section className="panel form-card">
    <div className="form-section-head"><h2>Resume</h2><p>PDF only, up to 5 MB. Your resume is visible to hiring managers for jobs you apply to.</p></div>
    {resume === undefined && <p>Loading resume…</p>}
    {resume === null && <p>No resume uploaded yet.</p>}
    {resume && <div className="profile-intro"><span className="company-mark"><Icon name="file" /></span><div><strong>{resume.filename}</strong><p>{Math.max(1, Math.round(resume.size_bytes / 1024))} KB · uploaded {formatDate(resume.uploaded_at)}</p></div></div>}
    <label className="field"><span>{resume ? "Replace resume" : "Upload resume"}</span>
      <input type="file" accept="application/pdf,.pdf" disabled={busy} onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; void handleFile(f); }} />
      <small>Only .pdf files are accepted.</small>
    </label>
    <div className="form-actions">
      {resume && <Button variant="secondary" disabled={busy} onClick={() => void download()}>Download</Button>}
      {resume && <Button variant="danger" disabled={busy} onClick={() => void remove()}>Delete</Button>}
    </div>
    {error && <p role="alert" className="error-text">{error}</p>}
    {notice && <div className="inline-success"><Icon name="check" size={17} /> {notice}</div>}
  </section>;
}

function ApplicationsPanel({ navigate }: { navigate: (s: Screen, jobId?: string) => void }) {
  const [items, setItems] = useState<ApiApplication[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    api.myApplications(1, 50).then((res) => {
      if (cancelled) return;
      setItems(res.items); setTotal(res.total); setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      setError(err instanceof Error ? err.message : "Could not load applications"); setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);
  const withdraw = async (id: string) => {
    setBusyId(id); setError(null);
    try {
      await api.withdrawApplication(id);
      setItems((prev) => prev.map((a) => (a.id === id ? { ...a, status: "withdrawn" } : a)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not withdraw this application");
    } finally { setBusyId(null); }
  };
  return <section className="panel table-panel">
    <div className="table-toolbar"><div className="panel-heading"><div><h2>My applications</h2><p>{loading ? "Loading…" : `${total} ${total === 1 ? "application" : "applications"} submitted`}</p></div></div></div>
    {loading && <p>Loading your applications…</p>}
    {error && <p role="alert" className="error-text">{error}</p>}
    {!loading && !error && items.length === 0 && <p>You haven’t applied to any internal jobs yet.</p>}
    {items.length > 0 && <div className="data-table">
      <div className="table-row table-head"><span>Job</span><span>Applied on</span><span>Status</span><span>Actions</span></div>
      {items.map((app) => <div className="table-row" key={app.id}>
        <span><strong>{app.job_title}</strong></span>
        <span>{formatDate(app.created_at)}</span>
        <span><Pill tone={statusTone(app.status)}>{app.status.replace("_", " ")}</Pill></span>
        <span><div className="row-actions">
          <button title="View job" onClick={() => navigate("job", app.job_id)}><Icon name="eye" size={17} /></button>
          {["submitted", "under_review", "shortlisted"].includes(app.status) &&
            <button className="danger" title="Withdraw application" disabled={busyId === app.id} onClick={() => void withdraw(app.id)}><Icon name="trash" size={17} /></button>}
        </div></span>
      </div>)}
    </div>}
    <div className="table-footer"><p>Showing {items.length ? `1–${items.length}` : "0"} of {total}</p></div>
  </section>;
}

/** Manage Jobs — live jobs with search, status filter, paging, edit and delete. */
function ManageJobsPanel({ navigate }: { navigate: (s: Screen) => void }) {
  const [items, setItems] = useState<ApiJob[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [editing, setEditing] = useState<ApiJob | null>(null);
  const [pendingDelete, setPendingDelete] = useState<ApiJob | null>(null);
  const pageSize = 8;

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.managedJobs({ q: query || undefined, status: status || undefined, page, page_size: pageSize })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages ?? Math.max(1, Math.ceil(res.total / pageSize)));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setTotalPages(1);
        setError(err instanceof Error ? err.message : "Could not load your jobs");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [query, status, page]);

  useEffect(() => {
    const timer = setTimeout(load, query ? 350 : 0);
    return () => clearTimeout(timer);
  }, [load, query]);

  const runAction = async <T,>(id: string, action: () => Promise<T>, message: string, onSuccess?: (result: T) => void) => {
    setBusyId(id);
    setError(null);
    setNotice(null);
    try {
      const result = await action();
      onSuccess?.(result);
      setNotice(message);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    const target = pendingDelete;
    setPendingDelete(null);
    await runAction(target.id, () => api.deleteJob(target.id), `"${target.title}" was deleted.`);
  };

  return <>
    {editing && <EditJobDialog job={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); setNotice("Job updated."); load(); }} />}
    {pendingDelete && <ConfirmDialog
      title="Delete this requisition?"
      body={`"${pendingDelete.title}" will be permanently removed. Jobs that already have applications or referrals must be closed instead of deleted.`}
      confirmLabel="Delete job"
      onCancel={() => setPendingDelete(null)}
      onConfirm={() => void confirmDelete()}
    />}
    <section className="panel table-panel">
      <div className="table-toolbar">
        <div className="search-box"><Icon name="search" /><input aria-label="Search jobs" placeholder="Search by title, team or location" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} /></div>
        <select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All Jobs</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
        <Button onClick={() => navigate("post-job")}><Icon name="plus" size={17} /> Post a job</Button>
      </div>
      {loading && <p style={{ padding: "0 20px" }}>Loading your requisitions...</p>}
      {!loading && error && <div style={{ padding: "0 20px" }}><p role="alert" className="error-text">{error}</p><Button variant="secondary" onClick={load}>Try again</Button></div>}
      {!loading && !error && notice && <div className="inline-success" style={{ margin: "10px 20px" }}><Icon name="check" size={17} /> {notice}</div>}
      {!loading && !error && items.length === 0 && <div style={{ padding: 20 }}><h2>No jobs found</h2><p>{query || status ? "No jobs match your search or filter." : "You haven't posted a job yet."}</p><Button onClick={() => navigate("post-job")}><Icon name="plus" size={17} /> Post your first job</Button></div>}
      {items.length > 0 && <div className="data-table">
        <div className="table-row table-head"><span>Job title</span><span>Status</span><span>Applicants</span><span>Created</span><span>Actions</span></div>
        {items.map((job) => <div className="table-row" key={job.id}>
          <span><strong>{job.title}</strong><small style={{ display: "block", color: "var(--muted)" }}>{job.team} · {job.location}</small></span>
          <span><Pill tone={jobStatusTone(job.status)}>{job.status === "open" ? "Open" : "Closed"}</Pill></span>
          <span>{job.applicant_count ?? 0}</span>
          <span>{formatDate(job.created_at)}</span>
          <span><div className="row-actions">
            <button title="View applicants" onClick={() => navigate("applicants")}><Icon name="users" size={17} /></button>
            <button title="Edit job" disabled={busyId === job.id || job.status === "closed"} onClick={() => setEditing(job)}><Icon name="edit" size={17} /></button>
            <button className="status-action" disabled={busyId === job.id} onClick={() => {
              const nextStatus: JobStatus = job.status === "open" ? "closed" : "open";
              const label = nextStatus === "closed" ? "closed" : "opened";
              void runAction(
                job.id,
                () => api.updateJobStatus(job.id, nextStatus),
                `"${job.title}" was ${label}.`,
                (result) => setItems((current) => current.map((item) => item.id === job.id ? result.job : item)),
              );
            }}>{job.status === "open" ? "Close" : "Open"}</button>
            <button className="danger" title="Delete job" disabled={busyId === job.id} onClick={() => setPendingDelete(job)}><Icon name="trash" size={17} /></button>
          </div></span>
        </div>)}
      </div>}
      <div className="table-footer">
        <p>Showing {items.length ? `${(page - 1) * pageSize + 1}-${(page - 1) * pageSize + items.length}` : "0"} of {total}</p>
        <div className="pagination mini">
          <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Previous</button>
          <button className="active">{page}</button>
          <span style={{ alignSelf: "center", fontSize: 10 }}>of {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</button>
        </div>
      </div>
    </section>
  </>;
}

function jobStatusTone(status: JobStatus): string {
  return status === "open" ? "teal" : "red";
}

/** Confirmation for destructive actions. */
function ConfirmDialog({ title, body, confirmLabel, onCancel, onConfirm }: { title: string; body: string; confirmLabel: string; onCancel: () => void; onConfirm: () => void }) {
  return <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={title}>
    <div className="modal-card modal-small">
      <h2>{title}</h2>
      <p>{body}</p>
      <div className="form-actions">
        <Button variant="danger" onClick={onConfirm}>{confirmLabel}</Button>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  </div>;
}

/** Referrals (hiring manager / HR) — live records with search, filter, paging, review. */
function ReferralsPanel({ navigate }: { navigate: (s: Screen, jobId?: string) => void }) {
  const [items, setItems] = useState<ApiReferral[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const pageSize = 8;

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.allReferrals({ q: query || undefined, status: status || undefined, page, page_size: pageSize })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages ?? Math.max(1, Math.ceil(res.total / pageSize)));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setTotalPages(1);
        setError(err instanceof Error ? err.message : "Could not load referrals");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [query, status, page]);

  useEffect(() => {
    const timer = setTimeout(load, query ? 350 : 0);
    return () => clearTimeout(timer);
  }, [load, query]);

  const review = async (referral: ApiReferral, nextStatus: string) => {
    setBusyId(referral.id);
    setError(null);
    setNotice(null);
    try {
      await api.updateReferralStatus(referral.id, nextStatus);
      setNotice(`Referral for ${referral.candidate_name} marked ${nextStatus}.`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the referral");
    } finally {
      setBusyId(null);
    }
  };

  const bonusTone = (bonus?: ApiReferral["bonus"]): string => {
    if (!bonus) return "amber";
    if (bonus.approval_status === "approved") return "teal";
    if (bonus.approval_status === "rejected") return "red";
    if (bonus.payment_status === "paid") return "teal";
    return "amber";
  };

  const bonusLabel = (bonus?: ApiReferral["bonus"]): string => {
    if (!bonus) return "No bonus recorded";
    if (bonus.approval_status === "approved") {
      return bonus.amount != null ? `Approved ${bonus.currency ?? "INR"} ${bonus.amount.toLocaleString("en-IN")}` : "Approved";
    }
    if (bonus.approval_status === "rejected") return "Rejected";
    return bonus.approval_status ?? "Pending";
  };

  return <section className="panel table-panel">
    <div className="table-toolbar">
      <div className="search-box"><Icon name="search" /><input aria-label="Search referrals" placeholder="Search by candidate name or email" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} /></div>
      <select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="eligible">Eligible</option>
        <option value="ineligible">Ineligible</option>
        <option value="interview">Interview</option>
        <option value="hired">Hired</option>
        <option value="rejected">Rejected</option>
      </select>
    </div>
    {loading && <p style={{ padding: "0 20px" }}>Loading referrals...</p>}
    {!loading && error && <div style={{ padding: "0 20px" }}><p role="alert" className="error-text">{error}</p><Button variant="secondary" onClick={load}>Try again</Button></div>}
    {!loading && !error && notice && <div className="inline-success" style={{ margin: "10px 20px" }}><Icon name="check" size={17} /> {notice}</div>}
    {!loading && !error && items.length === 0 && <div style={{ padding: 20 }}><h2>No referrals found</h2><p>{query || status ? "No referrals match your search or filter." : "No employees have referred a candidate to your roles yet."}</p></div>}
    {items.length > 0 && <div className="data-table">
      <div className="table-row table-head"><span>Candidate</span><span>Role</span><span>Referral status</span><span>Bonus status</span><span>Actions</span></div>
      {items.map((ref) => <div className="table-row" key={ref.id}>
        <span><strong>{ref.candidate_name}</strong><small style={{ display: "block", color: "var(--muted)" }}>{ref.referrer?.full_name ? `Referred by ${ref.referrer.full_name}` : "Referrer unavailable"}</small></span>
        <span>{ref.job_title ?? "General referral"}</span>
        <span><Pill tone={statusTone(ref.status)}>{ref.status.replace(/_/g, " ")}</Pill></span>
        <span><Pill tone={bonusTone(ref.bonus)}>{bonusLabel(ref.bonus)}</Pill></span>
        <span><div className="row-actions">
          <button title="View referral" onClick={() => navigate("referral-detail", ref.id)}><Icon name="eye" size={17} /></button>
          {ref.status === "pending" && <button title="Mark eligible" disabled={busyId === ref.id} onClick={() => void review(ref, "eligible")}><Icon name="check" size={17} /></button>}
          {ref.status === "pending" && <button className="danger" title="Mark ineligible" disabled={busyId === ref.id} onClick={() => void review(ref, "ineligible")}><Icon name="close" size={17} /></button>}
        </div></span>
      </div>)}
    </div>}
    <div className="table-footer">
      <p>Showing {items.length ? `${(page - 1) * pageSize + 1}-${(page - 1) * pageSize + items.length}` : "0"} of {total}</p>
      <div className="pagination mini">
        <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Previous</button>
        <button className="active">{page}</button>
        <span style={{ alignSelf: "center", fontSize: 10 }}>of {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</button>
      </div>
    </div>
  </section>;
}

/** My Referrals (employee) — the signed-in employee's own referral records. */
function MyReferralsPanel({ navigate }: { navigate: (s: Screen, jobId?: string) => void }) {
  const [items, setItems] = useState<ApiReferral[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 8;

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.myReferrals({ q: query || undefined, status: status || undefined, page, page_size: pageSize })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages ?? Math.max(1, Math.ceil(res.total / pageSize)));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setTotalPages(1);
        setError(err instanceof Error ? err.message : "Could not load your referrals");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [query, status, page]);

  useEffect(() => {
    const timer = setTimeout(load, query ? 350 : 0);
    return () => clearTimeout(timer);
  }, [load, query]);

  const bonusLabel = (bonus?: ApiReferral["bonus"]): string => {
    if (!bonus) return "No bonus recorded";
    if (bonus.approval_status === "approved") {
      return bonus.amount != null ? `${bonus.currency ?? "INR"} ${bonus.amount.toLocaleString("en-IN")} approved` : "Approved";
    }
    if (bonus.approval_status === "rejected") return "Not approved";
    return "Awaiting decision";
  };

  return <section className="panel table-panel">
    <div className="table-toolbar">
      <div className="search-box"><Icon name="search" /><input aria-label="Search my referrals" placeholder="Search by candidate name or email" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} /></div>
      <select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="eligible">Eligible</option>
        <option value="ineligible">Ineligible</option>
      </select>
      <Button onClick={() => navigate("refer")}><Icon name="plus" size={17} /> Refer someone</Button>
    </div>
    {loading && <p style={{ padding: "0 20px" }}>Loading your referrals...</p>}
    {!loading && error && <div style={{ padding: "0 20px" }}><p role="alert" className="error-text">{error}</p><Button variant="secondary" onClick={load}>Try again</Button></div>}
    {!loading && !error && items.length === 0 && <div style={{ padding: 20 }}><h2>No referrals yet</h2><p>{query || status ? "No referrals match your search or filter." : "Refer a colleague and track their progress here."}</p><Button onClick={() => navigate("refer")}><Icon name="plus" size={17} /> Refer someone</Button></div>}
    {items.length > 0 && <div className="data-table">
      <div className="table-row table-head"><span>Candidate</span><span>Role</span><span>Referral status</span><span>Bonus status</span><span>Actions</span></div>
      {items.map((ref) => <div className="table-row" key={ref.id}>
        <span><strong>{ref.candidate_name}</strong><small style={{ display: "block", color: "var(--muted)" }}>{ref.candidate_email}</small></span>
        <span>{ref.job_title ?? "General referral"}</span>
        <span><Pill tone={statusTone(ref.status)}>{ref.status.replace(/_/g, " ")}</Pill></span>
        <span><Pill tone={ref.bonus?.approval_status === "approved" ? "teal" : ref.bonus?.approval_status === "rejected" ? "red" : "amber"}>{bonusLabel(ref.bonus)}</Pill></span>
        <span><Button variant="ghost" onClick={() => navigate("referral-detail", ref.id)}>View <Icon name="chevron" size={15} /></Button></span>
      </div>)}
    </div>}
    <div className="table-footer">
      <p>Showing {items.length ? `${(page - 1) * pageSize + 1}-${(page - 1) * pageSize + items.length}` : "0"} of {total}</p>
      <div className="pagination mini">
        <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Previous</button>
        <button className="active">{page}</button>
        <span style={{ alignSelf: "center", fontSize: 10 }}>of {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</button>
      </div>
    </div>
  </section>;
}

/** Referral detail — real referral history and real bonus state. */
function ReferralDetailPanel({ referralId, manager, navigate }: { referralId?: string; manager: boolean; navigate: (s: Screen, jobId?: string) => void }) {
  const [referral, setReferral] = useState<ApiReferral | null>(null);
  const [loading, setLoading] = useState(Boolean(referralId));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!referralId) {
      setReferral(null);
      setLoading(false);
      return () => {};
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.getReferral(referralId)
      .then((res) => { if (!cancelled) setReferral(res.referral); })
      .catch((err: unknown) => { if (!cancelled) setError(err instanceof Error ? err.message : "Could not load this referral"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [referralId]);

  useEffect(() => load(), [load]);

  const decide = async (nextStatus: string) => {
    if (!referral) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const res = await api.updateReferralStatus(referral.id, nextStatus);
      setReferral(res.referral);
      setNotice(`Referral marked ${nextStatus}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the referral");
    } finally {
      setBusy(false);
    }
  };

  const back = () => navigate(manager ? "referrals" : "my-referrals");

  if (loading) return <><button className="back-link" onClick={back}>Back to referrals</button><section className="panel"><p>Loading referral...</p></section></>;
  if (error || !referral) return <><button className="back-link" onClick={back}>Back to referrals</button><section className="panel"><h2>Referral unavailable</h2><p role="alert" className="error-text">{error ?? "This referral could not be loaded."}</p><Button variant="secondary" onClick={load}>Try again</Button></section></>;

  const history = referral.status_history ?? [];
  const bonus = referral.bonus;
  const canReview = manager && referral.status !== "hired" && referral.status !== "rejected";

  return <>
    <button className="back-link" onClick={back}>Back to referrals</button>
    <div className="detail-layout">
      <section className="panel referral-main">
        <div className="person-head">
          <Avatar initials={initialsFor(referral.candidate_name)} />
          <div><h2>{referral.candidate_name}</h2><p>{referral.candidate_email}{referral.job_title ? ` · ${referral.job_title}` : " · General referral"}</p></div>
          <Pill tone={statusTone(referral.status)}>{referral.status.replace(/_/g, " ")}</Pill>
        </div>
        {referral.referrer?.full_name && <p style={{ color: "var(--muted)", fontSize: 11 }}>Referred by {referral.referrer.full_name}{referral.referrer.title ? ` · ${referral.referrer.title}` : ""}</p>}
        {referral.note && <p style={{ color: "var(--muted)", fontSize: 11 }}>Referrer note: {referral.note}</p>}
        {referral.eligibility_reason && <p style={{ color: "var(--muted)", fontSize: 11 }}>Review note: {referral.eligibility_reason}</p>}
        <h3>Referral progress</h3>
        {history.length === 0 && <p style={{ color: "var(--muted)", fontSize: 11 }}>No status changes recorded yet.</p>}
        {history.length > 0 && <div className="timeline">
          {history.slice(-4).map((entry, index) => <div className="done" key={`${entry.status}-${index}`}>
            <span><Icon name="check" size={14} /></span>
            <div><strong>{entry.status.replace(/_/g, " ")}</strong><small>{formatDate(entry.at)}</small></div>
          </div>)}
        </div>}
        <h3>History</h3>
        <div className="audit">
          <p><strong>Submitted</strong> <span>{formatDate(referral.created_at)}</span></p>
          {history.map((entry, index) => <p key={`audit-${index}`}><strong>Status changed to {entry.status.replace(/_/g, " ")}</strong>{entry.reason ? ` — ${entry.reason}` : ""} <span>{formatDate(entry.at)}</span></p>)}
        </div>
      </section>
      <aside className="panel bonus-card">
        <span className="gift-icon"><Icon name="gift" /></span>
        <p>Referral bonus</p>
        {bonus?.approval_status === "approved" && bonus.amount != null
          ? <h2>{bonus.currency ?? "INR"} {bonus.amount.toLocaleString("en-IN")}</h2>
          : <h2 className="bonus-none">Not set</h2>}
        <div><span>Referral status</span><Pill tone={statusTone(referral.status)}>{referral.status.replace(/_/g, " ")}</Pill></div>
        <div><span>Approval</span><strong>{bonus?.approval_status ?? "No decision recorded"}</strong></div>
        <div><span>Payment</span><strong>{bonus?.payment_status ? bonus.payment_status.replace(/_/g, " ") : "Not started"}</strong></div>
        {!bonus && <p style={{ color: "var(--muted)", fontSize: 10 }}>No bonus has been recorded for this referral. People &amp; Culture sets the amount explicitly — eligibility alone never creates one.</p>}
        {canReview && <div className="bonus-actions">
          <label className="field"><span>Update referral status</span>
            <select value="" disabled={busy} onChange={(e) => { if (e.target.value) void decide(e.target.value); }}>
              <option value="">Change status...</option>
              {referral.status === "pending" && <option value="eligible">Mark eligible</option>}
              {referral.status === "pending" && <option value="ineligible">Mark ineligible</option>}
              {(referral.status === "eligible" || referral.status === "ineligible") && <option value="pending">Send back to pending</option>}
            </select>
          </label>
        </div>}
        {!manager && <p style={{ color: "var(--muted)", fontSize: 10 }}>The hiring team reviews your referral. You'll be notified when its status changes.</p>}
        {notice && <div className="inline-success"><Icon name="check" size={17} /> {notice}</div>}
        {error && <p role="alert" className="error-text">{error}</p>}
      </aside>
    </div>
  </>;
}

function Planner() {
  const [generated, setGenerated] = useState(true);
  return <div className="planner-layout"><section className="panel planner-input"><span className="ai-icon"><Icon name="spark" /></span><h2>Your AI preparation partner</h2><p>Tell us what you want to focus on, and we’ll build a practical plan around your time.</p><label className="field"><span>Focus areas</span><div className="tag-input"><span>Portfolio story ×</span><span>Design leadership ×</span><input placeholder="Add focus area" /></div></label><label className="field"><span>Time available</span><select><option>3 days · 45 minutes per day</option><option>1 week · 30 minutes per day</option></select></label><Button className="full" onClick={() => setGenerated(true)}><Icon name="spark" size={17} /> Generate my plan</Button></section>{generated && <section className="panel plan-result"><div className="panel-heading"><div><Pill tone="blue">AI-generated plan</Pill><h2>3-day interview sprint</h2><p>Senior Product Designer · 2h 15m total</p></div><Button variant="secondary">Save plan</Button></div>{[["Day 1", "Shape your narrative", "45 min", ["Pick 2 projects with clear business outcomes", "Practice a 3-minute career walkthrough"]], ["Day 2", "Product & craft deep dive", "45 min", ["Explain one complex systems decision", "Prepare trade-offs and research evidence"]], ["Day 3", "Leadership & final rehearsal", "45 min", ["Practice stakeholder conflict scenarios", "Run a timed portfolio presentation"]]].map(([day, title, time, items]) => <div className="plan-day" key={String(day)}><span>{day}</span><div><h3>{title} <small>{time}</small></h3>{(items as string[]).map(x => <p key={x}><Icon name="check" size={15} />{x}</p>)}</div></div>)}</section>}</div>;
}

function AccessPage({ code, navigate }: { code: "403" | "404"; navigate: (s: Screen) => void }) {
  return <div className="access-page"><Brand /><span>{code}</span><h1>{code === "403" ? "You don’t have access" : "Page not found"}</h1><p>{code === "403" ? "This workspace or action isn’t available for your account." : "The page you’re looking for may have moved or no longer exists."}</p><Button onClick={() => navigate("dashboard")}>Return to dashboard</Button></div>;
}

export default function App() {
  return <AuthProvider><Shell /></AuthProvider>;
}

function Shell() {
  const { user, uiRole, loading, logout, applyUser } = useAuth();
  const [screen, setScreen] = useState<Screen>("login");
  const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined);
  const [dark, setDark] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const role = uiRole;
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  useEffect(() => {
    if (user) setScreen((s) => (s === "login" || s === "register" ? "dashboard" : s));
    else setScreen("login");
  }, [user]);
  const navigate = (s: Screen, jobId?: string) => {
    if (typeof jobId !== "undefined") setSelectedJobId(jobId);
    else if (s === "applicants") setSelectedJobId(undefined);
    setScreen(s); window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const goAuth = (s: Screen) => setScreen(s);
  if (!user) {
    if (screen === "register") return <Auth register onAuth={() => navigate("dashboard")} />;
    return <Auth register={false} onAuth={() => navigate("dashboard")} />;
  }
  if (loading) return <div className="access-page"><Brand /><h1>Restoring your session…</h1></div>;
  if (screen === "403" || screen === "404") return <AccessPage code={screen} navigate={navigate} />;
  // The signed-in account drives every screen. Nothing below derives identity
  // from the role or from a hardcoded sample person.
  const account = user;
  let content: ReactNode;
  if (screen === "dashboard") content = role === "employee" ? <EmployeeDashboard account={account} navigate={navigate} /> : <ManagerDashboard account={account} navigate={navigate} />;
  else if (screen === "jobs") content = <Jobs navigate={navigate} />;
  else if (screen === "job") content = <JobDetailApi navigate={navigate} jobId={selectedJobId ?? ""} />;
  else if (screen === "refer") content = <ReferForm navigate={navigate} prefillJobId={selectedJobId} />;
  else if (screen === "planner") content = <Planner />;
  else if (screen === "applications") content = <ApplicationsPanel navigate={navigate} />;
  else if (screen === "my-referrals") content = <MyReferralsPanel navigate={navigate} />;
  else if (screen === "referral-detail") content = <ReferralDetailPanel referralId={selectedJobId} manager={role === "manager"} navigate={navigate} />;
  else if (screen === "profile") content = <ProfilePage account={account} onSaved={applyUser} />;
  else if (screen === "post-job") content = <PostJobForm navigate={navigate} />;
  else if (screen === "manage-jobs") content = <ManageJobsPanel navigate={navigate} />;
  else if (screen === "applicants") content = <ApplicantsPanel jobId={selectedJobId} navigate={navigate} />;
  else if (screen === "referrals") content = <ReferralsPanel navigate={navigate} />;
  else content = <AccessPage code="404" navigate={navigate} />;
  const doLogout = async () => { await logout(); setSelectedJobId(undefined); navigate("login"); };
  return <div className="app-shell"><Sidebar account={account} role={role} screen={screen} navigate={navigate} open={drawer} close={() => setDrawer(false)} logout={() => void doLogout()} /><div className="app-main"><Topbar screen={screen} account={account} dark={dark} setDark={setDark} menu={() => setDrawer(true)} /><main className="page-content">{content}</main></div></div>;
}
