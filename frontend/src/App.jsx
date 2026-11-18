import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const onHash = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return hash;
}

const PAGE_SIZES = [25, 50, 100];

function Nav({ route }) {
  const links = [
    ["#/", "Search"],
    ["#/audits/new", "New audit"],
    ["#/dashboard", "Dashboard"],
  ];
  return (
    <nav className="tabs">
      {links.map(([href, label]) => (
        <a key={href} href={href} className={route === href ? "active" : ""}>
          {label}
        </a>
      ))}
    </nav>
  );
}

function SearchPage() {
  const [filters, setFilters] = useState({
    case_id: "",
    customer: "",
    tse: "",
    auditor: "",
    case_priority: "",
    customer_tier: "",
    audit_type: "",
    audit_date_from: "",
    audit_date_to: "",
    submitted_from: "",
    submitted_to: "",
    score_min: "",
    score_max: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [sort, setSort] = useState("submitted_at");
  const [sortDir, setSortDir] = useState("desc");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");

  const qs = useMemo(() => {
    const p = new URLSearchParams();
    p.set("page", String(page));
    p.set("page_size", String(pageSize));
    p.set("sort", sort);
    p.set("sort_dir", sortDir);
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== "" && v != null) p.set(k, v);
    });
    return p.toString();
  }, [filters, page, pageSize, sort, sortDir]);

  const load = useCallback(() => {
    setErr("");
    api
      .searchAudits(qs)
      .then(setResult)
      .catch((e) => setErr(e.message || "Search failed"));
  }, [qs]);

  useEffect(() => {
    load();
  }, [load]);

  function toggleSort(field) {
    if (sort === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSort(field);
      setSortDir("desc");
    }
  }

  const totalPages = result ? Math.max(1, Math.ceil(result.total / pageSize)) : 1;

  return (
    <>
      <section className="card">
        <h2>Audit search</h2>
        <div className="filter-grid">
          {[
            ["case_id", "Case ID"],
            ["customer", "Customer"],
            ["tse", "TSE"],
            ["auditor", "Auditor"],
            ["case_priority", "Priority"],
            ["customer_tier", "Customer tier"],
            ["audit_type", "Audit type"],
            ["audit_date_from", "Audit date from", "date"],
            ["audit_date_to", "Audit date to", "date"],
            ["submitted_from", "Submitted from", "date"],
            ["submitted_to", "Submitted to", "date"],
            ["score_min", "Score min", "number"],
            ["score_max", "Score max", "number"],
          ].map(([key, label, type = "text"]) => (
            <label key={key} className="field">
              {label}
              <input
                type={type}
                value={filters[key]}
                onChange={(e) => {
                  setFilters((f) => ({ ...f, [key]: e.target.value }));
                  setPage(1);
                }}
              />
            </label>
          ))}
        </div>
        <div className="actions">
          <button type="button" className="btn btn-primary" onClick={load}>
            Search
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => {
              setFilters({
                case_id: "",
                customer: "",
                tse: "",
                auditor: "",
                case_priority: "",
                customer_tier: "",
                audit_type: "",
                audit_date_from: "",
                audit_date_to: "",
                submitted_from: "",
                submitted_to: "",
                score_min: "",
                score_max: "",
              });
              setPage(1);
            }}
          >
            Clear
          </button>
        </div>
        {err && <p className="msg err">{err}</p>}
      </section>

      <section className="card table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Customer</th>
              <th>TSE</th>
              <th>Auditor</th>
              <th>Priority</th>
              <th>Tier</th>
              <th>Type</th>
              <th>
                <button type="button" onClick={() => toggleSort("audit_date")}>
                  Audit date {sort === "audit_date" ? (sortDir === "asc" ? "↑" : "↓") : ""}
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("score")}>
                  Score {sort === "score" ? (sortDir === "asc" ? "↑" : "↓") : ""}
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("submitted_at")}>
                  Submitted {sort === "submitted_at" ? (sortDir === "asc" ? "↑" : "↓") : ""}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {(result?.items || []).map((row) => (
              <tr key={row.id} onClick={() => (window.location.hash = `#/audits/${row.id}`)}>
                <td>{row.case_id}</td>
                <td>{row.customer}</td>
                <td>{row.tse}</td>
                <td>{row.auditor}</td>
                <td>{row.case_priority}</td>
                <td>{row.customer_tier}</td>
                <td>{row.audit_type || "—"}</td>
                <td>{row.audit_date}</td>
                <td>
                  {row.total_score}/{row.max_score} ({Math.round(Number(row.score_pct) * 100)}%)
                </td>
                <td>{new Date(row.submitted_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!result?.items?.length && <p className="meta">No audits found.</p>}
        <div className="pager">
          <span>
            {result ? `${result.total} result(s)` : "—"} · page {page} / {totalPages}
          </span>
          <label>
            Page size{" "}
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
            >
              {PAGE_SIZES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <button
            type="button"
            className="btn"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </section>
    </>
  );
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function NewAuditPage() {
  const [version, setVersion] = useState(null);
  const [meta, setMeta] = useState({
    case_id: "",
    audit_date: today(),
    auditor: "",
    tse: "",
    customer: "",
    case_priority: "",
    customer_tier: "",
    case_status: "",
    audit_type: "",
    strengths: "",
    areas_for_improvement: "",
    coaching_action: "",
    tse_acknowledged: "",
  });
  const [answers, setAnswers] = useState({});
  const [comments, setComments] = useState({});
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.latestQuestionnaires().then((list) => setVersion(list[0] || null));
  }, []);

  const questions = useMemo(() => {
    if (!version) return [];
    return version.sections.flatMap((s) =>
      s.questions.map((q) => ({ ...q, section_title: s.title }))
    );
  }, [version]);

  const preview = useMemo(() => {
    let total = 0;
    let max = 0;
    questions.forEach((q) => {
      const opt = q.options.find((o) => o.value === answers[q.id]);
      max += Math.max(...q.options.map((o) => o.score), 0);
      if (opt) total += opt.score;
    });
    return { total, max, pct: max ? Math.round((total / max) * 100) : 0 };
  }, [questions, answers]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    if (!version) return;
    const exists = await api.caseExists(meta.case_id);
    if (exists.exists) {
      setErr("This Case ID already has an audit.");
      return;
    }
    setBusy(true);
    try {
      const body = {
        ...meta,
        questionnaire_version_id: version.id,
        responses: questions.map((q) => ({
          question_id: q.id,
          response_value: answers[q.id] || "",
          comment: comments[q.id] || null,
        })),
      };
      const created = await api.submitAudit(body);
      setMsg(`Submitted (score ${Math.round(Number(created.score_pct) * 100)}%).`);
      window.location.hash = `#/audits/${created.id}`;
    } catch (ex) {
      const errors = ex.body?.detail?.errors;
      setErr(errors ? errors.join("; ") : ex.message || "Submit failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="grid-2" onSubmit={onSubmit}>
      <div>
        <section className="card">
          <h2>Case details</h2>
          <div className="filter-grid">
            {[
              ["case_id", "Case ID", true],
              ["audit_date", "Audit date", true, "date"],
              ["auditor", "Auditor", true],
              ["tse", "TSE / engineer", true],
              ["customer", "Customer", true],
              ["case_priority", "Case priority", true],
              ["customer_tier", "Customer tier", true],
              ["case_status", "Case status", false],
              ["audit_type", "Audit type", false],
            ].map(([key, label, req, type = "text"]) => (
              <label key={key} className="field">
                {label}
                {type === "text" && key === "case_priority" ? (
                  <select required={req} value={meta[key]} onChange={(e) => setMeta({ ...meta, [key]: e.target.value })}>
                    <option value="">Select</option>
                    {["P1", "P2", "P3", "P4"].map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                ) : type === "text" && key === "customer_tier" ? (
                  <select required={req} value={meta[key]} onChange={(e) => setMeta({ ...meta, [key]: e.target.value })}>
                    <option value="">Select</option>
                    <option>High-Priority</option>
                    <option>Standard</option>
                  </select>
                ) : (
                  <input
                    required={req}
                    type={type}
                    value={meta[key]}
                    onChange={(e) => setMeta({ ...meta, [key]: e.target.value })}
                  />
                )}
              </label>
            ))}
          </div>
        </section>

        {version?.sections.map((sec) => (
          <section key={sec.id} className="card">
            <h2>{sec.title}</h2>
            {sec.questions.map((q) => (
              <div key={q.id} className="q-row">
                <strong>
                  {q.number_label} — {q.title}
                </strong>
                <p style={{ margin: "0.25rem 0", color: "var(--muted)", fontSize: "0.9rem" }}>{q.criteria}</p>
                <div className="seg">
                  {q.options.map((o) => (
                    <button
                      key={o.value}
                      type="button"
                      className={
                        answers[q.id] === o.value
                          ? o.value === "Yes"
                            ? "sel-yes"
                            : o.value === "No"
                              ? "sel-no"
                              : "sel-na"
                          : ""
                      }
                      onClick={() => setAnswers((a) => ({ ...a, [q.id]: o.value }))}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
                <label className="field" style={{ marginTop: "0.35rem" }}>
                  Comment
                  <textarea
                    rows={2}
                    placeholder={answers[q.id] === "No" ? "Required for No" : "Optional"}
                    value={comments[q.id] || ""}
                    onChange={(e) => setComments((c) => ({ ...c, [q.id]: e.target.value }))}
                  />
                </label>
              </div>
            ))}
          </section>
        ))}

        <section className="card">
          <h2>Coaching notes</h2>
          {["strengths", "areas_for_improvement", "coaching_action"].map((key) => (
            <label key={key} className="field" style={{ marginBottom: "0.5rem" }}>
              {key.replace(/_/g, " ")}
              <textarea value={meta[key]} onChange={(e) => setMeta({ ...meta, [key]: e.target.value })} />
            </label>
          ))}
        </section>
      </div>

      <aside className="rail">
        <h2 style={{ marginTop: 0 }}>Score preview</h2>
        <p style={{ fontSize: "2rem", margin: "0.25rem 0", color: "var(--brand)" }}>{preview.pct}%</p>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          {preview.total} of {preview.max} marks
        </p>
        <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "1rem" }} disabled={busy}>
          {busy ? "Submitting…" : "Submit audit"}
        </button>
        {err && <p className="msg err">{err}</p>}
        {msg && <p className="msg ok">{msg}</p>}
      </aside>
    </form>
  );
}

function AuditDetailPage({ id }) {
  const [audit, setAudit] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api
      .getAudit(id)
      .then(setAudit)
      .catch((e) => setErr(e.message));
  }, [id]);
  if (err) return <p className="msg err">{err}</p>;
  if (!audit) return <p>Loading…</p>;
  return (
    <div>
      <section className="card">
        <h2>
          Case {audit.case_id} — {Math.round(Number(audit.score_pct) * 100)}%
        </h2>
        <p>
          {audit.customer} · {audit.tse} · Audited by {audit.auditor} on {audit.audit_date}
        </p>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          {audit.template_name} v{audit.version_number} · Submitted {new Date(audit.submitted_at).toLocaleString()}
        </p>
      </section>
      <section className="card">
        <h2>Responses</h2>
        {audit.responses.map((r) => (
          <div key={r.question_id} className="q-row">
            <strong>
              {r.number_label} — {r.title}
            </strong>
            <p>
              {r.response_value} ({r.points_earned} pts) · {r.section_title}
            </p>
            {r.comment && <p style={{ fontSize: "0.9rem" }}>Comment: {r.comment}</p>}
          </div>
        ))}
      </section>
    </div>
  );
}

function DashboardPage() {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.dashboard().then(setData);
  }, []);
  if (!data) return <p>Loading…</p>;
  return (
    <section className="card">
      <h2>Summary</h2>
      <p>
        {data.audit_count} audits · average score {data.avg_score_pct}%
      </p>
      {["by_auditor", "by_tse", "by_customer_tier"].map((key) => (
        <div key={key}>
          <h3>{key.replace(/_/g, " ")}</h3>
          <ul>
            {data[key].map((row) => (
              <li key={row.name}>
                {row.name}: {row.count} audits, avg {row.avg_score_pct}%
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function App() {
  const hash = useHashRoute();
  let page = <SearchPage />;
  const detail = hash.match(/^#\/audits\/(\d+)$/);
  if (hash === "#/audits/new") page = <NewAuditPage />;
  else if (detail) page = <AuditDetailPage id={detail[1]} />;
  else if (hash === "#/dashboard") page = <DashboardPage />;

  return (
    <div className="layout">
      <header className="app-bar">
        <h1>Case quality audit</h1>
        <Nav route={hash.split("?")[0] || "#/"} />
      </header>
      {page}
    </div>
  );
}

export default App;