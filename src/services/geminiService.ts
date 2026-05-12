import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

/**
 * Service for interacting with Gemini AI agents.
 */
export const geminiService = {
  /**
   * Generates a story based on a topic and groep level.
   */
  async generateStory(topic: string, groep: number) {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Schrijf een kort, spannend en leerzaam verhaal voor kinderen in Groep ${groep} over: ${topic}. Het verhaal moet in het Nederlands zijn, ongeveer 300 woorden lang, en eindigen met een kleine leerzame les.`,
      config: {
        systemInstruction: "Je bent een vriendelijke verhalenverteller voor Nederlandse basisschoolkinderen.",
        temperature: 0.8,
      },
    });
    return response.text;
  },

  /**
   * Generates a coloring page prompt (line art).
   */
  async generateColoringPrompt(topic: string) {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Create a detailed but clean line art coloring page description for: ${topic}. Simple shapes, no shading, thick outlines.`,
    });
    return response.text;
  },

  /**
   * Generates an image part using the image model.
   */
  async generateImage(prompt: string) {
     const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: {
        parts: [{ text: prompt + ", children's book illustration style, vibrant, playful, white background" }],
      },
    });

    for (const part of response.candidates[0].content.parts) {
      if (part.inlineData) {
        return `data:image/png;base64,${part.inlineData.data}`;
      }
    }
    return null;
  },

  /**
   * Generates a video based on a story/prompt.
   */
  async generateVideo(prompt: string) {
    const aiWithKey = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    return await aiWithKey.models.generateVideos({
      model: 'veo-3.1-lite-generate-preview',
      prompt: `Animated children's story illustration: ${prompt}, bright colors, simple shapes`,
      config: {
        numberOfVideos: 1,
        resolution: '720p',
        aspectRatio: '16:9'
      }
    });
  },

  /**
   * Status check for video operation.
   */
  async getVideoStatus(operation: any) {
    const aiWithKey = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    return await aiWithKey.operations.getVideosOperation({ operation });
  }
};
