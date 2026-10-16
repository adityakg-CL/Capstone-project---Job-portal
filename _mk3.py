import io

def W(path, text):
    io.open(path, 'w', encoding='utf-8', newline='').write(text)

W('_panels3.txt', r'''/** Referrals (hiring manager / HR) — live records with search, filter, paging, review. */
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
''')
print('part3a')
