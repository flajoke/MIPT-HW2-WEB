const SESSION_STORAGE_KEY = 'lvd-store-session-id';

const createSessionId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `frontend-${crypto.randomUUID()}`;
  }
  return `frontend-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export const getSessionId = () => {
  const existing = localStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) return existing;

  const nextSessionId = createSessionId();
  localStorage.setItem(SESSION_STORAGE_KEY, nextSessionId);
  return nextSessionId;
};
