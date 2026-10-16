import io

def W(path, text, mode='w'):
    io.open(path, mode, encoding='utf-8', newline='').write(text)

W('_panels1.txt', r'''/** Manage Jobs — live requisitions with search, status filter, paging, edit and delete. */
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

  const runAction = async (id: string, action: () => Promise<unknown>, message: string) => {
    setBusyId(id);
    setError(null);
    setNotice(null);
    try {
      await action();
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
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="pending_approval">Pending approval</option>
          <option value="approved">Approved</option>
          <option value="published">Published</option>
          <option value="rejected">Rejected</option>
          <option value="closed">Closed</option>
        </select>
        <Button onClick={() => navigate("post-job")}><Icon name="plus" size={17} /> Post a job</Button>
      </div>
''')
print('part1')
