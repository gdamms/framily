import { writable } from 'svelte/store';

export interface AuthState {
    token: string | null;
    isAuthenticated: boolean;
}

function createAuthStore() {
    const { subscribe, set, update } = writable<AuthState>({
        token: typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null,
        isAuthenticated: typeof window !== 'undefined' ? !!localStorage.getItem('auth_token') : false,
    });

    return {
        subscribe,
        setToken: (token: string) => {
            localStorage.setItem('auth_token', token);
            set({ token, isAuthenticated: true });
        },
        clearToken: () => {
            localStorage.removeItem('auth_token');
            set({ token: null, isAuthenticated: false });
        },
        getToken: (): string | null => {
            if (typeof window !== 'undefined') {
                return localStorage.getItem('auth_token');
            }
            return null;
        },
    };
}

export const authStore = createAuthStore();
