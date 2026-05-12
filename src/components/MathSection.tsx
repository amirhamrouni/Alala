import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Calculator, Trophy, Loader2 } from 'lucide-react';

interface MathSectionProps {
  groep: number;
  onSuccess: (coins: number) => void;
}

export default function MathSection({ groep, onSuccess }: MathSectionProps) {
  const [problem, setProblem] = useState({ q: '', a: 0 });
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<'success' | 'fail' | null>(null);

  const generateProblem = () => {
    let q = '';
    let a = 0;

    if (groep <= 2) {
      const n1 = Math.floor(Math.random() * 5) + 1;
      const n2 = Math.floor(Math.random() * 5);
      q = `${n1} + ${n2}`;
      a = n1 + n2;
    } else if (groep <= 4) {
      const n1 = Math.floor(Math.random() * 20);
      const n2 = Math.floor(Math.random() * 20);
      q = `${n1} + ${n2}`;
      a = n1 + n2;
    } else {
      const n1 = Math.floor(Math.random() * 12);
      const n2 = Math.floor(Math.random() * 12);
      q = `${n1} x ${n2}`;
      a = n1 * n2;
    }

    setProblem({ q, a });
    setUserAnswer('');
    setFeedback(null);
  };

  useEffect(() => {
    generateProblem();
  }, [groep]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (parseInt(userAnswer) === problem.a) {
      setFeedback('success');
      onSuccess(10);
      setTimeout(generateProblem, 2000);
    } else {
      setFeedback('fail');
      setTimeout(() => setFeedback(null), 1000);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4 md:p-8">
      <div className="bg-white rounded-[40px] p-8 md:p-12 shadow-2xl border-4 border-orange-200">
        <div className="flex items-center gap-6 mb-12">
          <div className="w-20 h-20 bg-orange-400 rounded-[2rem] flex items-center justify-center text-white shadow-lg border-b-4 border-orange-600">
            <Calculator size={40} />
          </div>
          <div>
            <h2 className="text-4xl font-black text-orange-900 leading-tight">Rekenen</h2>
            <p className="text-orange-600 font-bold tracking-wide">Word een echte sommen-kampioen!</p>
          </div>
        </div>

        <div className="flex flex-col items-center gap-12">
          <motion.div 
            key={problem.q}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-9xl font-black text-gray-800 tracking-tighter drop-shadow-lg"
          >
            {problem.q}<span className="text-orange-400">?</span>
          </motion.div>

          <form onSubmit={handleSubmit} className="w-full max-w-lg flex flex-col md:flex-row gap-4">
            <input
              type="number"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="Antwoord"
              autoFocus
              className="flex-1 px-8 py-6 rounded-3xl bg-orange-50 border-4 border-orange-100 focus:border-orange-400 outline-none transition-all text-5xl font-black text-orange-900 text-center"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              className="bg-orange-500 hover:bg-orange-600 text-white px-12 py-6 rounded-3xl font-black text-3xl shadow-xl border-b-8 border-orange-700 transition-all"
            >
              CHECK!
            </motion.button>
          </form>

          <AnimatePresence>
            {feedback === 'success' && (
              <motion.div
                initial={{ scale: 0, rotate: -20 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0 }}
                className="flex flex-col items-center gap-4 py-8"
              >
                <div className="bg-yellow-400 p-8 rounded-full shadow-xl ring-8 ring-white">
                  <Trophy size={80} className="text-white" />
                </div>
                <p className="text-orange-600 font-black text-4xl uppercase tracking-tighter">SUPER! +10 MUNTEN</p>
              </motion.div>
            )}
            {feedback === 'fail' && (
              <motion.div
                initial={{ x: -10 }}
                animate={{ x: 10 }}
                className="text-red-500 font-black text-2xl uppercase"
              >
                Oeps! Probeer het nog een keer!
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
