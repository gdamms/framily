import { writable, get } from 'svelte/store';
import { api, type UserInfo } from '$lib/api';

export interface AuthState {
    token: string | null;
    isAuthenticated: boolean;
    user: UserInfo | null;
    isLoading: boolean;
}

function createAuthStore() {
    const initialToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    
    const { subscribe, set, update } = writable<AuthState>({
        token: initialToken,
        isAuthenticated: !!initialToken,
        user: null,
        isLoading: !!initialToken,
    });

    // Load user info on initialization if token exists
    if (initialToken && typeof window !== 'undefined') {
        api.auth.me(initialToken)
            .then(user => {
                update(state => ({ ...state, user, isLoading: false }));
            })
            .catch(() => {
                // Token invalid, clear auth
                localStorage.removeItem('auth_token');
                set({ token: null, isAuthenticated: false, user: null, isLoading: false });
            });
    }

    return {
        subscribe,
        setToken: async (token: string) => {
            localStorage.setItem('auth_token', token);
            update(state => ({ ...state, token, isAuthenticated: true, isLoading: true }));
            
            try {
                const user = await api.auth.me(token);
                update(state => ({ ...state, user, isLoading: false }));
            } catch {
                update(state => ({ ...state, isLoading: false }));
            }
        },
        clearToken: () => {
            localStorage.removeItem('auth_token');
            set({ token: null, isAuthenticated: false, user: null, isLoading: false });
        },
        getToken: (): string | null => {
            if (typeof window !== 'undefined') {
                return localStorage.getItem('auth_token');
            }
            return null;
        },
        refreshUser: async () => {
            const state = get({ subscribe });
            if (state.token) {
                try {
                    const user = await api.auth.me(state.token);
                    update(s => ({ ...s, user }));
                } catch {
                    // Ignore errors
                }
            }
        },
    };
}

export const authStore = createAuthStore();
