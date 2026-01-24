import { createClient } from '@supabase/supabase-js'

// 1. Get the URL from the environment variables (Vite uses import.meta.env)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string

// 2. Get the API Key (ANON key is safe to use in the browser)
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

// 3. Initialize the Supabase client
// This 'supabase' object will be used throughout the React app to fetch data
export const supabase = createClient(supabaseUrl, supabaseAnonKey)