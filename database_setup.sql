-- Database Setup Script for Science Point Coaching Management System
-- Run this script in your Supabase SQL Editor

-- Enable UUID extension (useful for modern web apps, though we'll keep INTEGER IDs for now to match legacy data if needed, but SERIAL is standard for Postgres)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    father_name TEXT,
    roll INTEGER,
    school TEXT,
    contact TEXT,
    category TEXT, -- SSC or HSC
    ssc_year INTEGER,
    student_class TEXT, -- Renamed from 'class' to avoid keyword conflict
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster searching by roll/year
CREATE INDEX idx_students_roll_year ON students(ssc_year, category, roll);

-- 2. Exams Table
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    type TEXT, -- Weekly Test, Monthly Test, etc.
    number TEXT,
    subject TEXT,
    total_marks INTEGER,
    category TEXT,
    ssc_year INTEGER,
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Results Table
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    score REAL DEFAULT 0,
    written_score REAL DEFAULT 0,
    mcq_score REAL DEFAULT 0,
    percentage REAL,
    grade TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, student_id) -- Prevent duplicate results for same exam/student
);

-- 4. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    month TEXT,
    year INTEGER,
    due_amount REAL DEFAULT 0,
    paid_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'due', -- 'due' or 'paid'
    date DATE, -- Payment date
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, month, year) -- Prevent duplicate payment records
);

-- 5. Create a function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for students table
CREATE TRIGGER update_students_modtime
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
