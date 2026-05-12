/**
 * Educational Subjects supported by the platform.
 */
export enum Subject {
  DUTCH = "Nederlands",
  MATH = "Rekenen",
  WORLD = "Wereldoriëntatie",
  STORY = "AI Verhalen",
  ART = "Art Hoek",
}

/**
 * Dutch school Groep levels (1 to 8).
 */
export type Groep = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

/**
 * User Progress structure for Firebase.
 */
export interface UserProfile {
  uid: string;
  displayName: string;
  groep: Groep;
  coins: number;
  badges: string[];
  lastActive: string;
  avatarId: string;
}

/**
 * Educational Activity structure.
 */
export interface Activity {
  id: string;
  subject: Subject;
  groep: Groep;
  title: string;
  description: string;
  rewardPoints: number;
  type: 'quiz' | 'game' | 'story' | 'coloring';
}

/**
 * AI Generated Story structure.
 */
export interface GeneratedStory {
  id: string;
  title: string;
  content: string;
  imageUrl?: string;
  audioUrl?: string; // For TTS
  videoUrl?: string; // For Veo
  createdAt: string;
  userId: string;
}
