import { useEffect, useRef } from 'react';

export function useTabFocus(callback: () => void, isEnabled: boolean = true) {
  const timeoutRef = useRef<any>(null);

  useEffect(() => {
    if (!isEnabled || typeof window === 'undefined') return;

    const handleFocus = () => {
      // Small debounce to prevent accidental triggering during rapid tab switching
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        if (document.visibilityState === 'visible') {
          callback();
        }
      }, 500); 
    };

    document.addEventListener('visibilitychange', handleFocus);
    window.addEventListener('focus', handleFocus);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      document.removeEventListener('visibilitychange', handleFocus);
      window.removeEventListener('focus', handleFocus);
    };
  }, [callback, isEnabled]);
}
