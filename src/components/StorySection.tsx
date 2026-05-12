import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sparkles, Play, Image as ImageIcon, Loader2, Video } from 'lucide-react';
import { geminiService } from '../services/geminiService';
import { db, auth } from '../lib/firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { handleFirestoreError, OperationType } from '../lib/firestoreUtils';

export default function StorySection({ groep }: { groep: number }) {
  const [topic, setTopic] = useState('');
  const [story, setStory] = useState<string | null>(null);
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [generatingVideo, setGeneratingVideo] = useState(false);

  const handleCreate = async () => {
    if (!topic || !auth.currentUser) return;
    setLoading(true);
    setStory(null);
    setImage(null);
    setVideoUrl(null);
    try {
      const generatedStory = await geminiService.generateStory(topic, groep);
      const generatedImage = await geminiService.generateImage(`Illustration for a story about ${topic}`);
      
      setStory(generatedStory || 'Oeps, er ging iets mis.');
      setImage(generatedImage);

      // Save to Firebase
      const storyData = {
        userId: auth.currentUser.uid,
        title: topic,
        topic: topic,
        content: generatedStory,
        imageUrl: generatedImage,
        createdAt: serverTimestamp(),
      };
      await addDoc(collection(db, 'stories'), storyData);

    } catch (error) {
      console.error(error);
      handleFirestoreError(error, OperationType.WRITE, 'stories');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!story) return;
    setGeneratingVideo(true);
    try {
      const response = await geminiService.generateVideo(topic);
      alert("Animatie word gemaakt! Het duurt ongeveer 2 minuten.");
    } catch (err) {
       console.error(err);
       alert("Video maken mislukt. Controleer je Gemini API Key.");
    } finally {
      setGeneratingVideo(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-8">
      <div className="bg-white rounded-[40px] p-8 md:p-12 shadow-2xl border-4 border-purple-200">
        <div className="flex items-center gap-6 mb-12">
          <div className="w-20 h-20 bg-purple-500 rounded-[2rem] flex items-center justify-center text-white shadow-lg border-b-4 border-purple-700">
            <Sparkles size={40} />
          </div>
          <div>
            <h2 className="text-4xl font-black text-purple-900 leading-tight">Magische Verhalen</h2>
            <p className="text-purple-500 font-bold tracking-wide">Laat de AI een uniek verhaal voor jou schrijven!</p>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-6 mb-12">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Waar moet het verhaal over gaan? (bijv. Een robot op de maan)"
            className="flex-1 px-8 py-6 rounded-3xl bg-purple-50 border-4 border-purple-100 focus:border-purple-400 outline-none transition-all text-xl font-bold text-purple-900 placeholder:text-purple-200"
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCreate}
            disabled={loading}
            className="bg-purple-600 hover:bg-purple-700 text-white px-12 py-6 rounded-3xl font-black text-2xl shadow-xl border-b-8 border-purple-800 disabled:opacity-50 flex items-center justify-center gap-4"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Play fill="currentColor" />}
            VERTEL!
          </motion.button>
        </div>

        <AnimatePresence>
          {(story || loading) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-12"
            >
              {loading ? (
                <div className="py-24 flex flex-col items-center gap-8">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                    className="w-24 h-24 border-8 border-purple-100 border-t-purple-600 rounded-full"
                  />
                  <p className="text-purple-400 font-black text-2xl animate-pulse text-center leading-relaxed">
                    Verhaal smeden met sterrenstof...<br/>Even geduld!
                  </p>
                </div>
              ) : (
                <div className="grid lg:grid-cols-[1fr_400px] gap-12 items-start">
                  <div className="space-y-8">
                    <div className="bg-purple-50/50 p-10 rounded-[3rem] border-4 border-purple-100 text-2xl leading-relaxed text-purple-900 font-bold shadow-inner whitespace-pre-wrap">
                      {story}
                    </div>
                    {story && !generatingVideo && (
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleGenerateVideo}
                        className="flex items-center gap-4 bg-white border-4 border-purple-200 text-purple-600 px-10 py-5 rounded-[2rem] font-black group transition-all shadow-lg hover:bg-purple-50"
                      >
                        <Video size={32} className="group-hover:rotate-12 transition-transform" />
                        MAAK EEN ANIMATIE!
                      </motion.button>
                    )}
                    {generatingVideo && (
                      <div className="flex items-center gap-4 text-purple-600 font-black text-xl px-10">
                        <Loader2 className="animate-spin" size={32} />
                        Bezig met animeren...
                      </div>
                    )}
                  </div>
                  {image && (
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="sticky top-40"
                    >
                      <img
                        src={image}
                        alt="Story illustration"
                        className="w-full rounded-[3rem] shadow-2xl border-8 border-white ring-4 ring-purple-100"
                        referrerPolicy="no-referrer"
                      />
                    </motion.div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
