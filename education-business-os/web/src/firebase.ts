import { initializeApp } from "firebase/app";
import {
  initializeAppCheck,
  ReCaptchaEnterpriseProvider
} from "firebase/app-check";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

export const firebaseConfigured = Boolean(
  config.apiKey && config.authDomain && config.projectId && config.appId
);
const app = initializeApp(
  firebaseConfigured ? config : { projectId: "demo-education-business-os" }
);

// Initialize App Check before accessing Auth, Firestore or Functions.
if (firebaseConfigured) {
  const siteKey = import.meta.env.VITE_RECAPTCHA_ENTERPRISE_SITE_KEY;
  if (import.meta.env.DEV) {
    // SDK-generated debug token: register it in Firebase Console.
    // Never commit a token or ship a debug build to production.
    (globalThis as typeof globalThis & {
      FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string;
    }).FIREBASE_APPCHECK_DEBUG_TOKEN = true;
  } else if (!siteKey) {
    throw new Error(
      "VITE_RECAPTCHA_ENTERPRISE_SITE_KEY is required for production App Check."
    );
  }

  initializeAppCheck(app, {
    provider: new ReCaptchaEnterpriseProvider(siteKey || "local-debug-site-key-not-used"),
    isTokenAutoRefreshEnabled: true
  });
}

export const auth = getAuth(app);
export const db = getFirestore(app);
export const functions = getFunctions(app);
