import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};
export const firebaseConfigured = Boolean(config.apiKey && config.projectId && config.appId);
const app = initializeApp(firebaseConfigured ? config : { projectId: "demo-education-business-os" });
export const auth = getAuth(app);
export const db = getFirestore(app);
export const functions = getFunctions(app);
