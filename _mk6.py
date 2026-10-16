import io

def W(path, text):
    io.open(path, 'w', encoding='utf-8', newline='').write(text)

W('_panels5.txt', r'''/** Referral detail — real referral history and real bonus state. */
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
''')
print('part5a')
