/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { getFirestore, doc, getDocFromServer } from 'firebase/firestore';
import firebaseConfig from '../../firebase-applet-config.json';

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId); 
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

/**
 * Tests connection to Firestore.
 */
async function testConnection() {
  try {
    await getDocFromServer(doc(db, 'test', 'connection'));
  } catch (error) {
    if(error instanceof Error && error.message.includes('the client is offline')) {
      console.error("Please check your Firebase configuration or internet connection.");
    }
  }
}
testConnection();

let isLoggingIn = false;

export const loginWithGoogle = async () => {
  if (isLoggingIn) return;
  isLoggingIn = true;
  try {
    return await signInWithPopup(auth, googleProvider);
  } catch (error: any) {
    if (error.code === 'auth/cancelled-popup-request') {
      console.log('Login request was already pending.');
    } else if (error.code === 'auth/popup-closed-by-user') {
      console.log('User closed the login popup.');
    } else {
      throw error;
    }
  } finally {
    isLoggingIn = false;
  }
};
