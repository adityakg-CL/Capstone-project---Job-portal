import io

def A(path, text):
    io.open(path, 'a', encoding='utf-8', newline='').write(text)

A('_panels3.txt', r'''
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
''')
print('part3b')
