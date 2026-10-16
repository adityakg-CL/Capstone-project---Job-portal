import io

def A(path, text):
    io.open(path, 'a', encoding='utf-8', newline='').write(text)

A('_panels1.txt', r'''      {loading && <p style={{ padding: "0 20px" }}>Loading your requisitions...</p>}
      {!loading && error && <div style={{ padding: "0 20px" }}><p role="alert" className="error-text">{error}</p><Button variant="secondary" onClick={load}>Try again</Button></div>}
      {!loading && !error && notice && <div className="inline-success" style={{ margin: "10px 20px" }}><Icon name="check" size={17} /> {notice}</div>}
      {!loading && !error && items.length === 0 && <div style={{ padding: 20 }}><h2>No requisitions found</h2><p>{query || status ? "No jobs match your search or filter." : "You haven't posted a job yet."}</p><Button onClick={() => navigate("post-job")}><Icon name="plus" size={17} /> Post your first job</Button></div>}
      {items.length > 0 && <div className="data-table">
        <div className="table-row table-head"><span>Job title</span><span>Status</span><span>Applicants</span><span>Created</span><span>Actions</span></div>
        {items.map((job) => <div className="table-row" key={job.id}>
          <span><strong>{job.title}</strong><small style={{ display: "block", color: "var(--muted)" }}>{job.team} · {job.location}</small></span>
          <span><Pill tone={jobStatusTone(job.status ?? "draft")}>{(job.status ?? "draft").replace(/_/g, " ")}</Pill></span>
          <span>{job.applicant_count ?? 0}</span>
          <span>{formatDate(job.created_at)}</span>
          <span><div className="row-actions">
            <button title="View applicants" onClick={() => navigate("applicants")}><Icon name="users" size={17} /></button>
            <button title="Edit job" disabled={busyId === job.id || job.status === "closed" || job.status === "rejected"} onClick={() => setEditing(job)}><Icon name="edit" size={17} /></button>
            {job.status === "draft" && <button title="Submit for approval" disabled={busyId === job.id} onClick={() => void runAction(job.id, () => api.submitJob(job.id), `"${job.title}" was submitted for approval.`)}><Icon name="arrow" size={17} /></button>}
            {(job.status === "published" || job.status === "approved" || job.status === "pending_approval") && <button title="Close job" disabled={busyId === job.id} onClick={() => void runAction(job.id, () => api.closeJob(job.id), `"${job.title}" was closed.`)}><Icon name="clock" size={17} /></button>}
            {(job.status === "draft" || job.status === "rejected") && <button className="danger" title="Delete job" disabled={busyId === job.id} onClick={() => setPendingDelete(job)}><Icon name="trash" size={17} /></button>}
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

function jobStatusTone(status: string): string {
  if (status === "published") return "teal";
  if (status === "closed" || status === "rejected") return "red";
  if (status === "pending_approval") return "amber";
  if (status === "approved") return "blue";
  return "neutral";
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
''')
print('part2')
