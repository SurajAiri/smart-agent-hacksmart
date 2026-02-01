'use client';

/**
 * Internationalization (i18n) for Agent Dashboard
 * Supports English and Hindi
 */

export type Language = 'en' | 'hi';

export const translations = {
  en: {
    // Header
    'header.title': 'Agent Dashboard',
    'header.subtitle': 'QuickRide Support',
    'header.onCall': 'On Call',
    'header.participants': 'participant',
    'header.participantsPlural': 'participants',
    
    // Connection Status
    'status.connected': 'Connected',
    'status.reconnecting': 'Reconnecting...',
    'status.disconnected': 'Disconnected',
    
    // Call Controls
    'call.connectedTo': 'Connected to',
    'call.mute': 'Mute',
    'call.unmute': 'Unmute',
    'call.complete': 'Complete Call',
    'call.end': 'End Call',
    'call.joining': 'Joining call...',
    'call.startCall': 'Start Call',
    
    // Queue Panel
    'queue.title': 'Handoff Queue',
    'queue.waiting': 'waiting',
    'queue.noHandoffs': 'No pending handoffs',
    'queue.loading': 'Loading...',
    
    // Alert Card
    'alert.accept': 'Accept',
    'alert.assigned': 'Assigned',
    'alert.queuePosition': 'Queue',
    
    // Priority
    'priority.urgent': 'Urgent',
    'priority.high': 'High',
    'priority.medium': 'Medium',
    'priority.low': 'Low',
    
    // Trigger Types
    'trigger.explicit': 'Explicit Request',
    'trigger.sentiment': 'Negative Sentiment',
    'trigger.frustration': 'User Frustrated',
    'trigger.loop': 'Stuck in Loop',
    
    // Context Brief
    'brief.selectHandoff': 'Select a handoff to view details',
    'brief.driverInfo': 'Driver Info',
    'brief.name': 'Name',
    'brief.phone': 'Phone',
    'brief.city': 'City',
    'brief.language': 'Language',
    'brief.conversationHealth': 'Conversation Health',
    'brief.sentiment': 'Sentiment',
    'brief.confidence': 'AI Confidence',
    'brief.summary': 'Summary',
    'brief.stuckOn': 'Stuck on',
    'brief.suggestedActions': 'Suggested Actions',
    'brief.conversation': 'Conversation',
    'brief.turns': 'turns',
    'brief.driver': 'Driver',
    'brief.bot': 'Bot',
    'brief.botActions': 'Bot Actions',
    'brief.unknown': 'Unknown',
    
    // Sentiment
    'sentiment.positive': 'Positive',
    'sentiment.neutral': 'Neutral',
    'sentiment.negative': 'Negative',
    'sentiment.frustrated': 'Frustrated',
    
    // Languages
    'lang.english': 'English',
    'lang.hindi': 'Hindi',
    'lang.hinglish': 'Hinglish',
    
    // Actions
    'action.acceptCall': 'Accept & Join Call',
    'action.completeHandoff': 'Complete Handoff',
    
    // Time
    'time.ago': 'ago',
    'time.justNow': 'just now',
    
    // Errors
    'error.failedToLoad': 'Failed to load',
    'error.failedToConnect': 'Failed to connect',
  },
  
  hi: {
    // Header
    'header.title': 'एजेंट डैशबोर्ड',
    'header.subtitle': 'क्विकराइड सपोर्ट',
    'header.onCall': 'कॉल पर',
    'header.participants': 'प्रतिभागी',
    'header.participantsPlural': 'प्रतिभागी',
    
    // Connection Status
    'status.connected': 'कनेक्टेड',
    'status.reconnecting': 'फिर से कनेक्ट हो रहा है...',
    'status.disconnected': 'डिस्कनेक्टेड',
    
    // Call Controls
    'call.connectedTo': 'कनेक्टेड',
    'call.mute': 'म्यूट',
    'call.unmute': 'अनम्यूट',
    'call.complete': 'कॉल पूर्ण',
    'call.end': 'कॉल समाप्त',
    'call.joining': 'कॉल में शामिल हो रहे हैं...',
    'call.startCall': 'कॉल शुरू करें',
    
    // Queue Panel
    'queue.title': 'हैंडऑफ कतार',
    'queue.waiting': 'प्रतीक्षारत',
    'queue.noHandoffs': 'कोई लंबित हैंडऑफ नहीं',
    'queue.loading': 'लोड हो रहा है...',
    
    // Alert Card
    'alert.accept': 'स्वीकार करें',
    'alert.assigned': 'सौंपा गया',
    'alert.queuePosition': 'कतार',
    
    // Priority
    'priority.urgent': 'अत्यावश्यक',
    'priority.high': 'उच्च',
    'priority.medium': 'मध्यम',
    'priority.low': 'निम्न',
    
    // Trigger Types
    'trigger.explicit': 'स्पष्ट अनुरोध',
    'trigger.sentiment': 'नकारात्मक भावना',
    'trigger.frustration': 'उपयोगकर्ता निराश',
    'trigger.loop': 'लूप में फंसा',
    
    // Context Brief
    'brief.selectHandoff': 'विवरण देखने के लिए हैंडऑफ चुनें',
    'brief.driverInfo': 'ड्राइवर जानकारी',
    'brief.name': 'नाम',
    'brief.phone': 'फोन',
    'brief.city': 'शहर',
    'brief.language': 'भाषा',
    'brief.conversationHealth': 'बातचीत स्वास्थ्य',
    'brief.sentiment': 'भावना',
    'brief.confidence': 'AI विश्वास',
    'brief.summary': 'सारांश',
    'brief.stuckOn': 'फंसा हुआ',
    'brief.suggestedActions': 'सुझाई गई कार्रवाइयां',
    'brief.conversation': 'बातचीत',
    'brief.turns': 'बारी',
    'brief.driver': 'ड्राइवर',
    'brief.bot': 'बॉट',
    'brief.botActions': 'बॉट कार्रवाइयां',
    'brief.unknown': 'अज्ञात',
    
    // Sentiment
    'sentiment.positive': 'सकारात्मक',
    'sentiment.neutral': 'तटस्थ',
    'sentiment.negative': 'नकारात्मक',
    'sentiment.frustrated': 'निराश',
    
    // Languages
    'lang.english': 'अंग्रेज़ी',
    'lang.hindi': 'हिंदी',
    'lang.hinglish': 'हिंग्लिश',
    
    // Actions
    'action.acceptCall': 'स्वीकार करें और कॉल में शामिल हों',
    'action.completeHandoff': 'हैंडऑफ पूर्ण करें',
    
    // Time
    'time.ago': 'पहले',
    'time.justNow': 'अभी',
    
    // Errors
    'error.failedToLoad': 'लोड करने में विफल',
    'error.failedToConnect': 'कनेक्ट करने में विफल',
  },
} as const;

export type TranslationKey = keyof typeof translations.en;

export function t(key: TranslationKey, lang: Language = 'en'): string {
  return translations[lang][key] || translations.en[key] || key;
}

// Hook for React components
import { createContext, useContext, useState, ReactNode } from 'react';

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('en');
  
  const translate = (key: TranslationKey): string => {
    return t(key, language);
  };
  
  return (
    <I18nContext.Provider value={{ language, setLanguage, t: translate }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
