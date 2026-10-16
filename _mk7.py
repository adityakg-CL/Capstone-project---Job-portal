import io

def A(path, text):
    io.open(path, 'a', encoding='utf-8', newline='').write(text)

A('_panels5.txt', r'''
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
''')
print('part5b')
