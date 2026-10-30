import React from "react";
import { createRoot } from "react-dom/client";
import { getIdTokenResult, onAuthStateChanged, signInWithEmailAndPassword, signOut, User } from "firebase/auth";
import { collection, getDocs, limit, query, where } from "firebase/firestore";
import { httpsCallable } from "firebase/functions";
import { auth, db, firebaseConfigured, functions } from "./firebase";
import "./style.css";

type Role = "admin" | "instructor" | "student" | "unknown";
type Enrollment = { id: string; studentId?: string; batchId?: string; status?: string };

function App() {
  const [user, setUser] = React.useState<User | null>(auth.currentUser);
  const [role, setRole] = React.useState<Role>("unknown");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [rows, setRows] = React.useState<Enrollment[]>([]);
  const [error, setError] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => onAuthStateChanged(auth, async (nextUser) => {
    setUser(nextUser);
    if (!nextUser) { setRole("unknown"); setRows([]); return; }
    try {
      const token = await getIdTokenResult(nextUser, true);
      const claim = token.claims.role;
      setRole(claim === "admin" || claim === "instructor" || claim === "student" ? claim : "unknown");
    } catch { setRole("unknown"); }
  }), []);

  const refresh = React.useCallback(async () => {
    if (!user || !firebaseConfigured) return;
    try {
      const base = collection(db, "enrollments");
      const q = role === "admin" ? query(base, limit(100))
        : role === "instructor" ? query(base, where("instructorId", "==", user.uid), limit(100))
        : query(base, where("studentId", "==", user.uid), limit(50));
      const snap = await getDocs(q);
      setRows(snap.docs.map(d => ({ id: d.id, ...d.data() } as Enrollment)));
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load records"); }
  }, [user, role]);
  React.useEffect(() => { void refresh(); }, [refresh]);

  async function login(e: React.FormEvent) {
    e.preventDefault(); setError(""); setMessage("");
    try { await signInWithEmailAndPassword(auth, email, password); }
    catch (err) { setError(err instanceof Error ? err.message : "Sign-in failed"); }
  }
  async function invoke(name: string, data: Record<string, unknown>) {
    setBusy(true); setError(""); setMessage("");
    try {
      const fn = httpsCallable(functions, name);
      const result = await fn(data);
      setMessage(name + " completed: " + JSON.stringify(result.data));
      await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Operation failed"); }
    finally { setBusy(false); }
  }
  const Field = ({label, name, type = "text", required = true}: {label:string;name:string;type?:string;required?:boolean}) =>
    <label>{label}<input name={name} type={type} required={required}/></label>;

  return <main>
    <header><div><small>APT-FLUTTER-B5 · PILOT</small><h1>Education Business OS</h1><p>Course operations · Student experience · Evidence</p></div><span className="tag">Firebase</span></header>
    {!firebaseConfigured && <aside>Demo shell only: configure web/.env.local to connect a Firebase project. No live data is loaded.</aside>}
    {!user ? <section className="panel narrow"><h2>Sign in</h2><form onSubmit={login}>
      <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required /></label>
      <button disabled={!firebaseConfigured}>Sign in</button></form></section> :
    <>
      <section className="welcome"><div><small>AUTHENTICATED ACCOUNT · {role.toUpperCase()}</small><h2>{user.email}</h2><p>Permissions are enforced by Firebase custom claims and Firestore Rules.</p></div><button className="secondary" onClick={()=>signOut(auth)}>Sign out</button></section>
      {role === "unknown" && <aside>Account signed in but no recognized role claim was found. Ask an administrator to assign admin, instructor or student role server-side.</aside>}
      <section className="cards">
        <article><small>COURSE</small><h3>Flutter Foundation</h3><p>Batch 5</p></article>
        <article><small>START DATE</small><h3>7 Nov 2026</h3><p>12 weeks · 24 sessions</p></article>
        <article><small>LISTED FEE</small><h3>300,000 MMK</h3><p>Case-study configuration</p></article>
      </section>
      <section className="panel"><div className="sectionHead"><h2>Enrollment records</h2><button className="secondary" onClick={()=>void refresh()}>Refresh</button></div>
        {rows.length ? rows.map(x=><div className="record" key={x.id}><strong>{x.batchId ?? "Batch"}</strong><span>{x.studentId ?? ""}</span><span>{x.status ?? "unknown"}</span><code>{x.id}</code></div>) : <p>No enrollment records found for this account.</p>}
      </section>
      {(role === "admin" || role === "instructor") && <section className="panel"><h2>Operations</h2><div className="forms">
        {role === "admin" && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("createCourseBatch",{courseId:f.get("courseId"),courseName:f.get("courseName"),batchId:f.get("newBatchId"),startDate:f.get("startDate"),fee:Number(f.get("fee")),currency:"MMK",schedule:String(f.get("schedule")).split(",").map(x=>x.trim())});}}>
          <h3>Create course / batch</h3><Field label="Course ID" name="courseId"/><Field label="Course name" name="courseName"/><Field label="Batch ID" name="newBatchId"/><Field label="Start date (YYYY-MM-DD)" name="startDate"/><Field label="Fee (MMK)" name="fee" type="number"/><Field label="Weekdays (comma separated)" name="schedule"/><button disabled={busy}>Create course and batch</button>
        </form>}

        {role === "admin" && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("createEnrollment",{studentId:f.get("studentId"),batchId:f.get("batchId"),instructorId:f.get("instructorId")||null});}}>
          <h3>Create enrollment</h3><Field label="Student Auth UID" name="studentId"/><Field label="Batch ID" name="batchId"/><Field label="Instructor UID (optional)" name="instructorId" required={false}/><button disabled={busy}>Create enrollment</button>
        </form>}
        <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("recordPayment",{enrollmentId:f.get("enrollmentId"),amount:Number(f.get("amount")),method:f.get("method"),reference:f.get("reference")});}}>
          <h3>Record payment</h3><Field label="Enrollment ID" name="enrollmentId"/><Field label="Amount (MMK)" name="amount" type="number"/><label>Method<select name="method"><option value="cash">Cash</option><option value="bank_transfer">Bank transfer</option><option value="other">Other</option></select></label><Field label="Receipt/reference" name="reference" required={false}/><button disabled={busy}>Record pending payment</button>
        </form>
        {role === "admin" && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("verifyPayment",{paymentId:f.get("paymentId"),verified:f.get("verified")==="true",note:f.get("note")});}}>
          <h3>Verify payment</h3><Field label="Payment ID" name="paymentId"/><label>Decision<select name="verified"><option value="true">Verified</option><option value="false">Rejected</option></select></label><Field label="Verification note" name="note" required={false}/><button disabled={busy}>Submit verification</button>
        </form>}
        <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("markAttendance",{enrollmentId:f.get("enrollmentId"),sessionNo:Number(f.get("sessionNo")),status:f.get("status")});}}>
          <h3>Mark attendance</h3><Field label="Enrollment ID" name="enrollmentId"/><Field label="Session (1–24)" name="sessionNo" type="number"/><label>Status<select name="status"><option>present</option><option>absent</option><option>late</option><option>excused</option></select></label><button disabled={busy}>Save attendance</button>
        </form>
        <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("recordOutcome",{enrollmentId:f.get("enrollmentId"),outcome:f.get("outcome"),evidence:f.get("evidence")});}}>
          <h3>Record student outcome</h3><Field label="Enrollment ID" name="enrollmentId"/><label>Outcome<select name="outcome"><option value="completed">Completed</option><option value="not_completed">Not completed</option><option value="withdrawn">Withdrawn</option></select></label><label>Evidence note<textarea name="evidence" rows={3}/></label><button disabled={busy}>Save outcome</button>
        </form>
        <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("recordAssessment",{enrollmentId:f.get("enrollmentId"),projectName:f.get("projectName"),score:Number(f.get("score")),feedback:f.get("feedback")});}}>
          <h3>Record assessment</h3><Field label="Enrollment ID" name="enrollmentId"/><Field label="Project name" name="projectName"/><Field label="Score (0–100)" name="score" type="number"/><label>Feedback<textarea name="feedback" rows={3}/></label><button disabled={busy}>Save assessment</button>
        </form>
      </div></section>}
    </>}
    {message && <p className="success">{message}</p>}
    {error && <p className="error">{error}</p>}
    <footer>Prototype UI · No real student/payment records are seeded · Payment remains pending until independently verified.</footer>
  </main>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
