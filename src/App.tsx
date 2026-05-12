/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import Navigation from './components/Navigation';
import ProgressHeader from './components/ProgressHeader';
import StorySection from './components/StorySection';
import MathSection from './components/MathSection';
import ArtSection from './components/ArtSection';
import { Subject, Groep, UserProfile } from './types';
import { auth, db, loginWithGoogle } from './lib/firebase';
import { onAuthStateChanged, User } from 'firebase/auth';
import { doc, getDoc, setDoc, onSnapshot, updateDoc, serverTimestamp } from 'firebase/firestore';
import { LogIn, Sparkles, Loader2 } from 'lucide-react';
import { handleFirestoreError, OperationType } from './lib/firestoreUtils';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSubject, setActiveSubject] = useState<Subject | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        // Load or create profile
        const userDocRef = doc(db, 'users', firebaseUser.uid);
        try {
          const userDoc = await getDoc(userDocRef);
          if (userDoc.exists()) {
            setProfile(userDoc.data() as UserProfile);
          } else {
            const newProfile: UserProfile = {
              uid: firebaseUser.uid,
              displayName: firebaseUser.displayName || 'Ontdekker',
              groep: 3,
              coins: 100,
              badges: [],
              lastActive: new Date().toISOString(),
              avatarId: '1',
            };
            await setDoc(userDocRef, newProfile);
            setProfile(newProfile);
          }
        } catch (error) {
          handleFirestoreError(error, OperationType.GET, `users/${firebaseUser.uid}`);
        }
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Listen for profile changes (coins updates)
  useEffect(() => {
    if (!user) return;
    const userDocRef = doc(db, 'users', user.uid);
    const unsubscribe = onSnapshot(userDocRef, (docSnap) => {
      if (docSnap.exists()) {
        setProfile(docSnap.data() as UserProfile);
      }
    }, (error) => {
      handleFirestoreError(error, OperationType.LIST, `users/${user.uid}`);
    });
    return () => unsubscribe();
  }, [user]);

  const handleLevelUp = async (amount: number) => {
    if (!user || !profile) return;
    const userDocRef = doc(db, 'users', user.uid);
    try {
      await updateDoc(userDocRef, {
        coins: profile.coins + amount,
        lastActive: new Date().toISOString()
      });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`);
    }
  };

  const updateGroep = async (newGroep: Groep) => {
    if (!user || !profile) return;
    const userDocRef = doc(db, 'users', user.uid);
    try {
      await updateDoc(userDocRef, { groep: newGroep });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#E6F3FF] flex flex-col items-center justify-center gap-4">
        <Loader2 className="animate-spin text-blue-500" size={48} />
        <p className="text-blue-900 font-black text-xl">Laden...</p>
      </div>
    );
  }

  if (!user || !profile) {
    return (
      <div className="min-h-screen bg-[#E6F3FF] flex flex-col items-center justify-center p-8 text-center bg-cover bg-center" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1502082553048-f009c37129b9?q=80&w=2070&auto=format&fit=crop)' }}>
        <div className="absolute inset-0 bg-blue-900/40 backdrop-blur-sm" />
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="relative z-10 bg-white/90 p-12 rounded-[3.5rem] shadow-2xl border-8 border-white max-w-lg w-full"
        >
          <div className="w-24 h-24 bg-blue-500 rounded-3xl mx-auto mb-8 flex items-center justify-center text-white shadow-xl">
            <Sparkles size={48} />
          </div>
          <h1 className="text-5xl font-black text-blue-900 mb-4">Welkom bij de Slimme Ontdekkers!</h1>
          <p className="text-gray-600 font-bold mb-8 text-lg">Hét avontuur voor nieuwsgierige kinderen.</p>
          <button
            onClick={loginWithGoogle}
            className="w-full flex items-center justify-center gap-4 bg-white border-4 border-gray-100 hover:border-blue-400 p-6 rounded-3xl text-xl font-black text-gray-700 transition-all shadow-xl hover:shadow-blue-200"
          >
            <LogIn />
            Inloggen met Meester/Juf
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F0F7FF] overflow-x-hidden selection:bg-blue-200">
      <div className="fixed inset-0 z-0 opacity-40">
        <div className="absolute inset-0 bg-gradient-radial from-blue-400/10 via-transparent to-transparent" />
      </div>

      <ProgressHeader 
        coins={profile.coins} 
        groep={profile.groep} 
        userName={profile.displayName} 
      />

      <main className="relative z-10 min-h-screen pt-32 pb-32 px-6">
        <AnimatePresence mode="wait">
          {!activeSubject ? (
            <motion.div
              key="world-map"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1 }}
              className="max-w-7xl mx-auto h-[calc(100vh-200px)] grid grid-cols-12 grid-rows-6 gap-4"
            >
              {/* Primary AI Agent Section: Story Generator */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveSubject(Subject.STORY)}
                className="col-span-12 md:col-span-6 row-span-4 bg-white rounded-[40px] border-4 border-purple-200 p-8 flex flex-col relative overflow-hidden group text-left"
              >
                <div className="absolute top-0 right-0 p-6">
                  <span className="bg-purple-100 text-purple-600 px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">AI Avontuur</span>
                </div>
                <div className="flex-grow flex flex-col justify-center">
                  <h2 className="text-4xl md:text-5xl font-black text-purple-900 mb-4 leading-tight">
                    Maak je eigen <br />
                    <span className="text-purple-500">AI Verhaal</span>
                  </h2>
                  <p className="text-gray-500 font-bold max-w-sm mb-8 text-lg">
                    De AI-Agent wacht op jouw ideeën om een nieuwe wereld te bouwen!
                  </p>
                  <div className="flex gap-4">
                    <div className="bg-purple-600 text-white px-8 py-4 rounded-2xl font-black border-b-4 border-purple-800 shadow-lg">
                      START NU
                    </div>
                  </div>
                </div>
                <div className="absolute bottom-8 right-8 text-8xl transition-transform group-hover:scale-110 group-hover:rotate-6">✨</div>
              </motion.button>

              {/* Math (Rekenen) */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveSubject(Subject.MATH)}
                className="col-span-6 md:col-span-3 row-span-2 bg-[#FFEDD5] rounded-[40px] border-4 border-[#FED7AA] p-8 flex flex-col justify-between text-left relative overflow-hidden group"
              >
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">🧮</div>
                <div>
                  <h3 className="text-2xl font-black text-orange-900 leading-tight">Rekenen</h3>
                  <p className="text-sm font-bold text-orange-700 opacity-80">Tafels & Sommen</p>
                </div>
                <div className="w-full bg-white h-3 rounded-full overflow-hidden mt-4 border-2 border-orange-200 shadow-inner">
                  <div className="bg-orange-500 h-full w-[75%] rounded-full shadow-lg" />
                </div>
              </motion.button>

              {/* Language (Taal) */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveSubject(Subject.DUTCH)}
                className="col-span-6 md:col-span-3 row-span-2 bg-[#DBEAFE] rounded-[40px] border-4 border-[#BFDBFE] p-8 flex flex-col justify-between text-left relative overflow-hidden group"
              >
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">📚</div>
                <div>
                  <h3 className="text-2xl font-black text-blue-900 leading-tight">Taal & Lezen</h3>
                  <p className="text-sm font-bold text-blue-700 opacity-80">Spelling & Woorden</p>
                </div>
                <div className="w-full bg-white h-3 rounded-full overflow-hidden mt-4 border-2 border-blue-200 shadow-inner">
                  <div className="bg-blue-500 h-full w-[40%] rounded-full shadow-lg" />
                </div>
              </motion.button>

              {/* Coloring (Kleuren) */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveSubject(Subject.ART)}
                className="col-span-6 md:col-span-3 row-span-4 bg-[#FCE7F3] rounded-[40px] border-4 border-[#FBCFE8] p-8 flex flex-col text-center group"
              >
                <div className="flex-grow flex flex-col items-center justify-center gap-6">
                  <div className="text-7xl group-hover:scale-110 transition-transform">🎨</div>
                  <h3 className="text-3xl font-black text-pink-900">Kleurboek</h3>
                  <p className="text-pink-700 font-bold text-sm max-w-[150px]">Gebruik AI om kleurplaten te maken!</p>
                </div>
                <div className="w-full bg-pink-500 text-white py-4 rounded-2xl font-black border-b-4 border-pink-700 shadow-lg group-hover:bg-pink-600 transition-colors">
                  OPEN PALET
                </div>
              </motion.button>

              {/* Rewards / Shop */}
              <div className="col-span-12 md:col-span-6 row-span-2 bg-[#DCFCE7] rounded-[40px] border-4 border-[#BBF7D0] p-8 flex items-center gap-8 relative overflow-hidden">
                <div className="hidden sm:flex h-full aspect-square bg-white rounded-3xl items-center justify-center text-5xl shadow-[0_4px_0_0_#A7F3D0] border-2 border-green-100">🏆</div>
                <div className="flex-grow">
                  <h3 className="text-3xl font-black text-green-900 leading-tight">Mijn Beloningen</h3>
                  <p className="text-green-700 font-bold mb-4">Nog 50 sterren voor een nieuwe avatar!</p>
                  <div className="flex gap-3">
                    {[1, 2, 3].map(i => (
                       <div key={i} className={`w-10 h-10 rounded-xl ${i < 3 ? 'bg-green-200 shadow-inner' : 'bg-green-100 border-2 border-dashed border-green-300'} flex items-center justify-center text-green-600 font-bold`}>
                         {i < 3 ? '✨' : ''}
                       </div>
                    ))}
                  </div>
                </div>
                <button className="bg-white text-green-600 px-8 py-4 rounded-2xl font-black border-b-4 border-gray-200 hover:bg-gray-50 transition-colors shadow-lg">
                  WINKEL
                </button>
              </div>

              {/* Level Selector (Custom Quiz/Settings Replacement) */}
              <div className="col-span-6 md:col-span-3 row-span-2 bg-[#F3E8FF] rounded-[40px] border-4 border-[#E9D5FF] p-8 flex flex-col justify-center items-center text-center group">
                 <h3 className="text-lg font-black text-purple-900 uppercase tracking-tighter mb-4">Mijn Niveau</h3>
                 <div className="flex flex-wrap justify-center gap-2">
                    {[1,2,3,4,5,6,7,8].map(g => (
                       <button
                         key={g}
                         onClick={() => updateGroep(g as Groep)}
                         className={`w-9 h-9 rounded-xl flex items-center justify-center font-black transition-all ${
                           profile.groep === g ? 'bg-purple-600 text-white shadow-lg scale-110' : 'bg-white text-purple-300 hover:bg-purple-50 border-2 border-purple-100'
                         }`}
                       >
                         {g}
                       </button>
                    ))}
                 </div>
                 <p className="text-purple-500 font-black text-xs uppercase mt-4 tracking-widest">Groep {profile.groep}</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="active-section"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              className="min-h-screen pb-32"
            >
              <button
                onClick={() => setActiveSubject(null)}
                className="fixed top-32 left-12 bg-white/80 p-4 rounded-2xl shadow-lg border-2 border-gray-100 hover:bg-white transition-all z-40"
              >
                ← Terug naar Map
              </button>

              {activeSubject === Subject.STORY && <StorySection groep={profile.groep} />}
              {activeSubject === Subject.MATH && <MathSection groep={profile.groep} onSuccess={handleLevelUp} />}
              {activeSubject === Subject.ART && <ArtSection />}
              {/* Fallback for other subjects */}
              {(activeSubject === Subject.DUTCH || activeSubject === Subject.WORLD) && (
                <div className="flex flex-col items-center justify-center py-40 gap-8">
                  <h2 className="text-4xl font-black text-blue-900">Dit eiland wordt nog gebouwd! 🏗️</h2>
                  <p className="text-blue-500 font-bold">Het AI team werkt hard aan nieuwe opdrachten.</p>
                  <button 
                    onClick={() => setActiveSubject(null)}
                    className="bg-blue-500 text-white px-8 py-4 rounded-2xl font-black text-xl shadow-xl hover:bg-blue-600 transition-all"
                  >
                    Ga terug naar het vasteland
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Navigation 
        activeSubject={activeSubject} 
        onSelectSubject={setActiveSubject} 
      />
    </div>
  );
}

