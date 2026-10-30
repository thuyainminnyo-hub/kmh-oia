import React from "react";
import { createRoot } from "react-dom/client";
import { onAuthStateChanged, signInWithEmailAndPassword, signOut } from "firebase/auth";
import { collection, getDocs, limit, query, where } from "firebase/firestore";
import { auth, db, firebaseConfigured } from "./firebase";
import "./style.css";

function App() {
  const [user, setUser] = React.useState(auth.currentUser);
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [rows, setRows] = React.useState<any[]>([]);
  const [error, setError] = React.useState("");
  React.useEffect(() => onAuthStateChanged(auth, setUser), []);
  React.useEffect(() => {
    if (!user || !firebaseConfigured) { setRows([]); return; }
    getDocs(query(collection(db, "enrollments"), where("studentId", "==", user.uid), limit(50)))
      .then(s => setRows(s.docs.map(d => ({ id: d.id, ...d.data() }))))
      .catch(e => setError(e.message));
  }, [user]);
  async function login(e: React.FormEvent) {
    e.preventDefault(); setError("");
    try { await signInWithEmailAndPassword(auth, email, password); }
    catch (err) { setError(err instanceof Error ? err.message : "Sign-in failed"); }
  }
  return <main>
    <header><div><small>APT-FLUTTER-B5 · PILOT</small><h1>Education Business OS</h1><p>Course operations · Student experience · Evidence</p></div><span className="tag">Firebase</span></header>
    {!firebaseConfigured && <aside>Demo shell only: configure web/.env.local to connect a real Firebase project. No live data is loaded.</aside>}
    {!user ? <section className="panel narrow"><h2>Sign in</h2><form onSubmit={login}>
      <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required /></label>
      <button disabled={!firebaseConfigured}>Sign in</button></form>{error && <p className="error">{error}</p>}</section> :
    <><section className="welcome"><div><small>AUTHENTICATED ACCOUNT</small><h2>{user.email}</h2><p>Enrollment records are read under Firestore authorization rules.</p></div><button className="secondary" onClick={()=>signOut(auth)}>Sign out</button></section>
    <section className="cards"><article><small>COURSE</small><h3>Flutter Foundation</h3><p>Batch 5</p></article><article><small>START DATE</small><h3>7 Nov 2026</h3><p>12 weeks · 24 sessions</p></article><article><small>LISTED FEE</small><h3>300,000 MMK</h3><p>Case-study configuration</p></article></section>
    <section className="panel"><h2>My enrollments</h2>{rows.length ? rows.map(x=><p key={x.id}>{x.batchId} · {x.status}</p>) : <p>No enrollment records found for this account.</p>}</section></>}
    <footer>Prototype UI · No real student/payment records are seeded · Never enter production data in this demo shell.</footer>
    {error && user && <p className="error">{error}</p>}
  </main>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
