import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Book, Calculator, Globe, PenTool, Sparkles, Trophy, Settings } from 'lucide-react';
import { Subject } from '../types';

interface NavigationProps {
  activeSubject: Subject | null;
  onSelectSubject: (subject: Subject) => void;
}

const navItems = [
  { subject: Subject.DUTCH, icon: Book, color: 'bg-blue-400', label: 'Taal & Lezen' },
  { subject: Subject.MATH, icon: Calculator, color: 'bg-green-400', label: 'Rekenen' },
  { subject: Subject.WORLD, icon: Globe, color: 'bg-orange-400', label: 'Ontdekken' },
  { subject: Subject.STORY, icon: Sparkles, color: 'bg-purple-400', label: 'AI Verhalen' },
  { subject: Subject.ART, icon: PenTool, color: 'bg-pink-400', label: 'Kleurhoek' },
];

export default function Navigation({ activeSubject, onSelectSubject }: NavigationProps) {
  return (
    <footer className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <div className="bg-white rounded-full px-8 py-3 flex gap-8 md:gap-12 shadow-lg border-2 border-blue-50">
        {navItems.map((item) => {
          const isActive = activeSubject === item.subject;
          const Icon = item.icon;

          return (
            <motion.button
              key={item.subject}
              id={`nav-${item.subject.toLowerCase()}`}
              whileHover={{ y: -5 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onSelectSubject(item.subject)}
              className={`flex flex-col items-center transition-all duration-300 ${
                isActive ? 'text-blue-600' : 'text-gray-400 opacity-60 hover:opacity-100 hover:text-blue-400'
              }`}
            >
              <Icon size={24} />
              <span className="text-[10px] font-black uppercase mt-1">{item.label.split(' ')[0]}</span>
              {isActive && (
                <motion.div
                  layoutId="active-nav-dot"
                  className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1"
                />
              )}
            </motion.button>
          );
        })}
        {activeSubject && (
           <motion.button
            whileHover={{ y: -5 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onSelectSubject(null as any)}
            className="flex flex-col items-center text-gray-400 opacity-60 hover:opacity-100"
          >
            <div className="w-6 h-6 flex items-center justify-center text-xl">🏠</div>
            <span className="text-[10px] font-black uppercase mt-1">Home</span>
          </motion.button>
        )}
      </div>
    </footer>
  );
}
