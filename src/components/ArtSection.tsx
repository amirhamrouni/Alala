import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Palette, Play, Loader2, Printer, Download } from 'lucide-react';
import { geminiService } from '../services/geminiService';

export default function ArtSection() {
  const [prompt, setPrompt] = useState('');
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!prompt) return;
    setLoading(true);
    try {
      const coloringImage = await geminiService.generateImage(`Line art coloring page for children, high contrast, black and white only, thick lines, no shading, simple background: ${prompt}`);
      setImage(coloringImage);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4 md:p-8">
      <div className="bg-white rounded-[40px] p-8 md:p-12 shadow-2xl border-4 border-pink-200">
        <div className="flex items-center gap-6 mb-12">
          <div className="w-20 h-20 bg-pink-500 rounded-[2rem] flex items-center justify-center text-white shadow-lg border-b-4 border-pink-700">
            <Palette size={40} />
          </div>
          <div>
            <h2 className="text-4xl font-black text-pink-900 leading-tight">Kleur Paradijs</h2>
            <p className="text-pink-600 font-bold tracking-wide">Ontwerp je eigen kleurplaat en print hem uit!</p>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-6 mb-12">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Wat wil je kleuren? (bijv. Een lieve draak)"
            className="flex-1 px-8 py-6 rounded-3xl bg-pink-50 border-4 border-pink-100 focus:border-pink-400 outline-none transition-all text-xl font-bold text-pink-900 placeholder:text-pink-200"
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleGenerate}
            disabled={loading}
            className="bg-pink-600 hover:bg-pink-700 text-white px-12 py-6 rounded-3xl font-black text-2xl shadow-xl border-b-8 border-pink-800 disabled:opacity-50 flex items-center justify-center gap-4"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Play fill="currentColor" />}
            ONTWERP!
          </motion.button>
        </div>

        <AnimatePresence>
          {image ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center gap-12"
            >
              <div className="bg-white p-8 rounded-[3rem] shadow-inner border-4 border-gray-100 ring-8 ring-pink-50 max-w-2xl w-full">
                <img
                  src={image}
                  alt="Coloring Page"
                  className="w-full rounded-2xl"
                  referrerPolicy="no-referrer"
                />
              </div>
              
              <div className="flex gap-6">
                <button 
                   onClick={() => window.print()}
                   className="flex items-center gap-4 bg-gray-900 text-white px-12 py-5 rounded-3xl font-black text-xl hover:bg-gray-800 transition-all shadow-xl"
                >
                  <Printer size={28} /> Printen
                </button>
                <a 
                  href={image} 
                  download="mijn-kleurplaat.png"
                  className="flex items-center gap-4 bg-pink-100 text-pink-600 px-12 py-5 rounded-3xl font-black text-xl hover:bg-pink-200 transition-all shadow-lg"
                >
                  <Download size={28} /> Opslaan
                </a>
              </div>
            </motion.div>
          ) : loading && (
            <div className="py-24 flex flex-col items-center gap-8">
              <div className="relative">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                  className="w-28 h-28 border-8 border-pink-100 border-t-pink-500 rounded-full"
                />
                <Palette className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-pink-300" size={48} />
              </div>
              <p className="text-pink-400 font-black text-2xl animate-pulse uppercase tracking-widest text-center">De potloden worden geslepen...</p>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
