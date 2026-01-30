import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';
import type { Session, User } from '@supabase/supabase-js';

type AuthContextType = {
    session: Session | null;
    user: User | null;
    userName: string | null;            // New
    userRole: string | null;
    userStatus: string | null;
    loading: boolean;
    signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [session, setSession] = useState<Session | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [userName, setUserName] = useState<string | null>(null); // New
    const [userRole, setUserRole] = useState<string | null>(null);
    const [userStatus, setUserStatus] = useState<string | null>(null); // 'pending', 'approved', 'rejected'
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // 1. Check active session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);
            if (session?.user) {
                fetchUserProfile(session.user.id);
            } else {
                setLoading(false);
            }
        });

        // 2. Listen for changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);
            if (session?.user) {
                fetchUserProfile(session.user.id);
            } else {
                setUserName(null);
                setUserRole(null);
                setUserStatus(null);
                setLoading(false);
            }
        });

        return () => subscription.unsubscribe();
    }, []);

    const fetchUserProfile = async (userId: string) => {
        try {
            // We link on 'auth_id' based on our new schema
            const { data, error } = await supabase
                .from('users')
                .select('role_id, status, user_name, roles(role_name)')
                .eq('auth_id', userId)
                .single();

            if (error) {
                console.error("Error fetching user profile:", error);
            } else if (data) {
                // Assuming data.roles is because of the join, or we might need to adjust based on exact return
                // simple join syntax: select('..., roles(role_name)')
                // data.roles will be an object { role_name: '...' } or array depending on relation 
                // Let's assume One-to-One or Many-to-One returns object
                const roleName = (data.roles as any)?.role_name || 'student'; // Default fallback
                setUserName(data.user_name);
                setUserRole(roleName.toLowerCase());
                setUserStatus(data.status);
            }
        } catch (err) {
            console.error("Unexpected error fetching profile:", err);
        } finally {
            setLoading(false);
        }
    };

    const signOut = async () => {
        await supabase.auth.signOut();
        setUserName(null);
        setUserRole(null);
        setUserStatus(null);
    };

    return (
        <AuthContext.Provider value={{ session, user, userName, userRole, userStatus, loading, signOut }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
