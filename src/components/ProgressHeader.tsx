import React from 'react';
import { motion } from 'motion/react';
import { Coins, Award, Star, User } from 'lucide-react';

interface ProgressHeaderProps {
  coins: number;
  groep: number;
  userName: string;
}

export default function ProgressHeader({ coins, groep, userName }: ProgressHeaderProps) {
  return (
    <header className="fixed top-6 left-1/2 -translate-x-1/2 w-[95%] max-w-6xl z-50">
      <nav className="flex items-center justify-between bg-white rounded-3xl p-4 shadow-[0_8px_0_0_#E0EEFF] border-2 border-[#D0E4FF]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-orange-400 rounded-2xl flex items-center justify-center text-white text-2xl font-bold border-b-4 border-orange-600 shadow-inner">
            {userName.charAt(0)}
          </div>
          <div>
            <h1 className="text-xl font-black text-blue-900 leading-tight">Hallo, {userName}!</h1>
            <p className="text-xs font-bold text-blue-400 uppercase tracking-wider">Groep {groep} • De Slimme Ontdekker</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4 md:gap-6">
          <div className="hidden sm:flex items-center bg-yellow-100 px-4 py-2 rounded-full border-2 border-yellow-200">
            <span className="text-xl mr-2">⭐</span>
            <span className="font-black text-yellow-700">1,240</span>
          </div>
          <div className="flex items-center bg-blue-50 px-4 py-2 rounded-full border-2 border-blue-100">
            <span className="text-xl mr-2">🪙</span>
            <span className="font-black text-blue-700">{coins}</span>
          </div>
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-2xl font-black border-b-4 border-green-700 transition-all text-xs md:text-sm whitespace-nowrap"
          >
            OUDER LOGIN
          </motion.button>
        </div>
      </nav>
    </header>
  );
}
