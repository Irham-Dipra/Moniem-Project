import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';
import type { Session, User } from '@supabase/supabase-js';

type AuthContextType = {
    session: Session | null;
    user: User | null;
    userName: string | null;
    dbUserId: number | null;            // New: The integer ID from users table
    userRole: string | null;
    userStatus: string | null;
    loading: boolean;
    signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [session, setSession] = useState<Session | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [userName, setUserName] = useState<string | null>(null);
    const [dbUserId, setDbUserId] = useState<number | null>(null); // New
    const [userRole, setUserRole] = useState<string | null>(null);
    const [userStatus, setUserStatus] = useState<string | null>(null);
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
                setDbUserId(null);
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
                .select('user_id, role_id, status, user_name, roles(role_name)')
                .eq('auth_id', userId)
                .single();

            if (error) {
                console.error("Error fetching user profile:", error);
            } else if (data) {
                const roleName = (data.roles as any)?.role_name || 'student';
                setUserName(data.user_name);
                setDbUserId(data.user_id); // Set the DB ID
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
        setDbUserId(null);
        setUserRole(null);
        setUserStatus(null);
    };

    return (
        <AuthContext.Provider value={{ session, user, userName, dbUserId, userRole, userStatus, loading, signOut }}>
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
