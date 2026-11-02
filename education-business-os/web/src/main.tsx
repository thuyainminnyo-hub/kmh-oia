import React from "react";
import { createRoot } from "react-dom/client";
import { onAuthStateChanged, signInWithEmailAndPassword, signOut, User } from "firebase/auth";
import { collection, getDocs, limit, query, QueryConstraint, where } from "firebase/firestore";
import { httpsCallable } from "firebase/functions";
import { auth, db, firebaseConfigured, functions } from "./firebase";
import "./style.css";

type Role = "admin" | "academic_manager" | "instructor" | "finance" | "student" | "creator" | "moderator" | "unknown";
type Membership = { organizationId: string; role: Role; status: string; organizationName?: string };
type Enrollment = { id: string; organizationId?: string; studentId?: string; batchId?: string; status?: string };
type OrganizationMember = { uid: string; role: Role; status: string; organizationName?: string };

function App() {
  const [user, setUser] = React.useState<User | null>(auth.currentUser);
  const [memberships, setMemberships] = React.useState<Membership[]>([]);
  const [organizationId, setOrganizationId] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [rows, setRows] = React.useState<Enrollment[]>([]);
  const [organizationMembers, setOrganizationMembers] = React.useState<OrganizationMember[]>([]);
  const [error, setError] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const activeMembership = memberships.find(m => m.organizationId === organizationId && m.status === "active");
  const role: Role = activeMembership?.role ?? "unknown";
  const organizationName = activeMembership?.organizationName ?? organizationId;

  React.useEffect(() => onAuthStateChanged(auth, async (nextUser) => {
    setUser(nextUser);
    setMemberships([]);
    setOrganizationId("");
    setRows([]);
    setError("");
    if (!nextUser) return;
    try {
      const membershipCollection = collection(db, "userOrganizationMemberships", nextUser.uid, "organizations");
      const snapshot = await getDocs(query(membershipCollection, limit(50)));
      const items = snapshot.docs.map(d => ({ ...d.data(), organizationId: d.id } as Membership))
        .filter(m => m.status === "active");
      setMemberships(items);
      if (items.length) setOrganizationId(items[0].organizationId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load organization memberships.");
    }
  }), []);

  const refreshMembers = React.useCallback(async () => {
    if (!user || !organizationId || role !== "admin") {
      setOrganizationMembers([]);
      return;
    }
    try {
      const membersRef = collection(db, "organizations", organizationId, "members");
      const snapshot = await getDocs(query(membersRef, limit(200)));
      setOrganizationMembers(snapshot.docs.map(d => ({ ...d.data(), uid: d.id } as OrganizationMember)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load organization members.");
    }
  }, [user, organizationId, role]);

  React.useEffect(() => { void refreshMembers(); }, [refreshMembers]);

  const refresh = React.useCallback(async () => {
    if (!user || !firebaseConfigured || !organizationId || role === "unknown" || role === "finance" || role === "creator" || role === "moderator") {
      setRows([]);
      return;
    }
    try {
      const base = collection(db, "enrollments");
      const constraints: QueryConstraint[] = [where("organizationId", "==", organizationId)];
      if (role === "instructor") constraints.push(where("instructorId", "==", user.uid));
      if (role === "student") constraints.push(where("studentId", "==", user.uid));
      constraints.push(limit(role === "student" ? 50 : 100));
      const snap = await getDocs(query(base, ...constraints));
      setRows(snap.docs.map(d => ({ id: d.id, ...d.data() } as Enrollment)));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load organization records.");
    }
  }, [user, organizationId, role]);

  React.useEffect(() => { void refresh(); }, [refresh]);

  async function login(e: React.FormEvent) {
    e.preventDefault(); setError(""); setMessage("");
    try { await signInWithEmailAndPassword(auth, email, password); }
    catch (err) { setError(err instanceof Error ? err.message : "Sign-in failed"); }
  }

  async function invoke(name: string, data: Record<string, unknown>) {
    if (!organizationId) { setError("Choose an organization before using this operation."); return; }
    setBusy(true); setError(""); setMessage("");
    try {
      const fn = httpsCallable(functions, name);
      const result = await fn({ ...data, organizationId });
      setMessage(name + " completed: " + JSON.stringify(result.data));
      await Promise.all([refresh(), refreshMembers()]);
    } catch (err) { setError(err instanceof Error ? err.message : "Operation failed"); }
    finally { setBusy(false); }
  }

  const Field = ({label, name, type = "text", required = true}: {label:string;name:string;type?:string;required?:boolean}) =>
    <label>{label}<input name={name} type={type} required={required}/></label>;
  const canManageAcademic = role === "admin" || role === "instructor" || role === "academic_manager";
  const canFinance = role === "admin" || role === "finance";
  const canRecordPayment = role === "admin" || role === "instructor" || role === "finance";

  return <main>
    <header><div><small>APT-FLUTTER-B5 · PILOT</small><h1>Education Business OS</h1><p>Course operations · Student experience · Evidence</p></div><span className="tag">Firebase</span></header>
    {!firebaseConfigured && <aside>Demo shell only: configure web/.env.local to connect a Firebase project. No live data is loaded.</aside>}
    {!user ? <section className="panel narrow"><h2>Sign in</h2><form onSubmit={login}>
      <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required /></label>
      <button disabled={!firebaseConfigured}>Sign in</button></form></section> :
    <>
      <section className="welcome">
        <div><small>AUTHENTICATED ACCOUNT · {role.toUpperCase()}</small><h2>{user.email}</h2>
          <p>Organization-scoped access · {organizationName || "No organization selected"}</p>
        </div>
        <div className="welcomeActions">
          {memberships.length > 0 && <label className="orgPicker">Organization
            <select value={organizationId} onChange={e=>setOrganizationId(e.target.value)}>
              {memberships.map(m=><option key={m.organizationId} value={m.organizationId}>{m.organizationName ?? m.organizationId}</option>)}
            </select>
          </label>}
          <button className="secondary" onClick={()=>signOut(auth)}>Sign out</button>
        </div>
      </section>
      {role === "unknown" && <aside>No active organization membership was found. Ask your organization's administrator to add your account.</aside>}
      {role !== "unknown" && <section className="cards">
        <article><small>WORKSPACE</small><h3>{organizationName}</h3><p>Organization: {organizationId}</p></article>
        <article><small>ROLE</small><h3>{role.replace("_", " ")}</h3><p>Permissions are scoped to this organization.</p></article>
        <article><small>MEMBERSHIPS</small><h3>{memberships.length}</h3><p>Active organization workspaces</p></article>
      </section>}
      {role === "admin" && <section className="panel"><div className="sectionHead"><h2>Organization members · {organizationName}</h2><button className="secondary" onClick={()=>void refreshMembers()}>Refresh members</button></div>
        <div className="forms">
          <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("setOrganizationMember",{uid:f.get("memberUid"),role:f.get("memberRole"),status:f.get("memberStatus")});e.currentTarget.reset();}}>
            <h3>Add / update member</h3>
            <Field label="Existing Firebase Auth UID" name="memberUid"/>
            <label>Organization role<select name="memberRole"><option value="student">Student</option><option value="instructor">Instructor</option><option value="finance">Finance</option><option value="academic_manager">Academic manager</option><option value="creator">Creator</option><option value="moderator">Moderator</option><option value="admin">Admin</option></select></label>
            <label>Membership status<select name="memberStatus"><option value="active">Active</option><option value="suspended">Suspended</option></select></label>
            <button disabled={busy}>Save organization membership</button>
          </form>
        </div>
        {organizationMembers.length ? organizationMembers.map(m=><div className="record" key={m.uid}><strong>{m.uid}</strong><span>{m.role}</span><span>{m.status}</span><code>{organizationId}</code></div>) : <p>No members loaded for this organization.</p>}
        <small>For this pilot, the user must already exist in Firebase Authentication. A secure invitation flow can replace UID entry later.</small>
      </section>}
            {(role === "admin" || role === "academic_manager" || role === "instructor" || role === "student") &&
      <section className="panel"><div className="sectionHead"><h2>Enrollment records · {organizationName}</h2><button className="secondary" onClick={()=>void refresh()}>Refresh</button></div>
        {rows.length ? rows.map(x=><div className="record" key={x.id}><strong>{x.batchId ?? "Batch"}</strong><span>{x.studentId ?? ""}</span><span>{x.status ?? "unknown"}</span><code>{x.id}</code></div>) : <p>No enrollment records found for this account in this organization.</p>}
      </section>}
      {(role === "admin" || role === "instructor" || role === "academic_manager" || canFinance) && <section className="panel"><h2>Operations</h2><div className="forms">
        {role === "admin" && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("createCourseBatch",{courseId:f.get("courseId"),courseName:f.get("courseName"),batchId:f.get("newBatchId"),startDate:f.get("startDate"),fee:Number(f.get("fee")),currency:"MMK",schedule:String(f.get("schedule")).split(",").map(x=>x.trim())});}}>
          <h3>Create course / batch</h3><Field label="Course ID" name="courseId"/><Field label="Course name" name="courseName"/><Field label="Batch ID" name="newBatchId"/><Field label="Start date (YYYY-MM-DD)" name="startDate"/><Field label="Fee (MMK)" name="fee" type="number"/><Field label="Weekdays (comma separated)" name="schedule"/><button disabled={busy}>Create course and batch</button>
        </form>}

        {role === "admin" && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("createEnrollment",{studentId:f.get("studentId"),batchId:f.get("batchId"),instructorId:f.get("instructorId")||null});}}>
          <h3>Create enrollment</h3><Field label="Student Auth UID" name="studentId"/><Field label="Batch ID" name="batchId"/><Field label="Instructor UID (optional)" name="instructorId" required={false}/><button disabled={busy}>Create enrollment</button>
        </form>}
        {canRecordPayment && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("recordPayment",{enrollmentId:f.get("enrollmentId"),amount:Number(f.get("amount")),method:f.get("method"),reference:f.get("reference")});}}>
          <h3>Record payment</h3><Field label="Enrollment ID" name="enrollmentId"/><Field label="Amount (MMK)" name="amount" type="number"/><label>Method<select name="method"><option value="cash">Cash</option><option value="bank_transfer">Bank transfer</option><option value="other">Other</option></select></label><Field label="Receipt/reference" name="reference" required={false}/><button disabled={busy}>Record pending payment</button>
        </form>}
        {canFinance && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("verifyPayment",{paymentId:f.get("paymentId"),verified:f.get("verified")==="true",note:f.get("note")});}}>
          <h3>Verify payment</h3><Field label="Payment ID" name="paymentId"/><label>Decision<select name="verified"><option value="true">Verified</option><option value="false">Rejected</option></select></label><Field label="Verification note" name="note" required={false}/><button disabled={busy}>Submit verification</button>
        </form>}
        {canManageAcademic && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("markAttendance",{enrollmentId:f.get("enrollmentId"),sessionNo:Number(f.get("sessionNo")),status:f.get("status")});}}>
          <h3>Mark attendance</h3><Field label="Enrollment ID" name="enrollmentId"/><Field label="Session (1–24)" name="sessionNo" type="number"/><label>Status<select name="status"><option>present</option><option>absent</option><option>late</option><option>excused</option></select></label><button disabled={busy}>Save attendance</button>
        </form>}
        {canManageAcademic && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("recordOutcome",{enrollmentId:f.get("enrollmentId"),outcome:f.get("outcome"),evidence:f.get("evidence")});}}>
          <h3>Record student outcome</h3><Field label="Enrollment ID" name="enrollmentId"/><label>Outcome<select name="outcome"><option value="completed">Completed</option><option value="not_completed">Not completed</option><option value="withdrawn">Withdrawn</option></select></label><label>Evidence note<textarea name="evidence" rows={3}/></label><button disabled={busy}>Save outcome</button>
        </form>}
        {canManageAcademic && <form onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);void invoke("recordAssessment",{enrollmentId:f.get("enrollmentId"),projectName:f.get("projectName"),score:Number(f.get("score")),feedback:f.get("feedback")});}}>
          <h3>Record assessment</h3><Field label="Enrollment ID" name="enrollmentId"/><Field label="Project name" name="projectName"/><Field label="Score (0–100)" name="score" type="number"/><label>Feedback<textarea name="feedback" rows={3}/></label><button disabled={busy}>Save assessment</button>
        </form>}
      </div></section>}
    </>}
    {message && <p className="success">{message}</p>}
    {error && <p className="error">{error}</p>}
    <footer>Prototype UI · Organization-scoped access · Synthetic data only · Payment remains pending until independently verified.</footer>
  </main>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
