
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Roles Table
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(role_id) ON DELETE SET NULL
);

-- 3. Batch Table
CREATE TABLE IF NOT EXISTS batch (
    batch_id SERIAL PRIMARY KEY,
    batch_name VARCHAR(100) NOT NULL
);

-- 4. Program Table
CREATE TABLE IF NOT EXISTS program (
    program_id SERIAL PRIMARY KEY,
    program_name VARCHAR(100) NOT NULL,
    batch_id INTEGER REFERENCES batch(batch_id) ON DELETE SET NULL,
    monthly_fee DECIMAL(10, 2) DEFAULT 0,
    start_date DATE,
    end_date DATE
);

-- 5. Teacher Table
CREATE TABLE IF NOT EXISTS teacher (
    teacher_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    contact VARCHAR(20),
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE
);

-- 6. Teacher Program Enrollment Table
CREATE TABLE IF NOT EXISTS teacher_program_enrollment (
    teacher_id INTEGER REFERENCES teacher(teacher_id) ON DELETE CASCADE,
    program_id INTEGER REFERENCES program(program_id) ON DELETE CASCADE,
    field VARCHAR(100),
    PRIMARY KEY (teacher_id, program_id)
);

-- 7. Student Table
CREATE TABLE IF NOT EXISTS student (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    fathers_name VARCHAR(100),
    school VARCHAR(100),
    contact VARCHAR(20),
    roll_no INTEGER,
    class INTEGER,
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Enrollment Table (Links Students to Programs)
CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES student(student_id) ON DELETE CASCADE,
    program_id INTEGER REFERENCES program(program_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    -- status column dropped
);

-- 9. Exam Table
CREATE TABLE IF NOT EXISTS exam (
    exam_id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES program(program_id) ON DELETE CASCADE,
    exam_name VARCHAR(100) NOT NULL,
    exam_date DATE,
    exam_type VARCHAR(50), -- e.g., 'Weekly', 'Monthly'
    subject VARCHAR(100),
    total_marks DECIMAL(10, 2) NOT NULL
);

-- 10. Student Individual Result Table
CREATE TABLE IF NOT EXISTS student_individual_result (
    result_id SERIAL PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollment(enrollment_id) ON DELETE CASCADE,
    exam_id INTEGER REFERENCES exam(exam_id) ON DELETE CASCADE,
    written_marks DECIMAL(5, 2) DEFAULT 0,
    mcq_marks DECIMAL(5, 2) DEFAULT 0,
    total_score DECIMAL(5, 2) GENERATED ALWAYS AS (written_marks + mcq_marks) STORED, -- Auto-calculated if supported, otherwise remove GENERATED clause and insert manually
    UNIQUE(enrollment_id, exam_id)
);

-- Note: If your Postgres version doesn't support GENERATED ALWAYS AS ... STORED, use this definition instead:
-- CREATE TABLE IF NOT EXISTS student_individual_result (
--     result_id SERIAL PRIMARY KEY,
--     enrollment_id INTEGER REFERENCES enrollment(enrollment_id) ON DELETE CASCADE,
--     exam_id INTEGER REFERENCES exam(exam_id) ON DELETE CASCADE,
--     written_marks DECIMAL(5, 2) DEFAULT 0,
--     mcq_marks DECIMAL(5, 2) DEFAULT 0,
--     total_score DECIMAL(5, 2),
--     UNIQUE(enrollment_id, exam_id)
-- );


-- 11. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id SERIAL PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollment(enrollment_id) ON DELETE CASCADE,
    status VARCHAR(20), -- e.g., 'Present', 'Absent', 'Late'
    date DATE DEFAULT CURRENT_DATE
);

-- 12. Payment Table
CREATE TABLE IF NOT EXISTS payment (
    payment_id SERIAL PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollment(enrollment_id) ON DELETE CASCADE,
    paid_amount DECIMAL(10, 2) DEFAULT 0,
    paid_amount DECIMAL(10, 2) DEFAULT 0,
    -- due_amount dropped
    month INTEGER,
    year INTEGER,
    transaction_group_id UUID, -- For grouping bulk payments
    status VARCHAR(20), -- e.g., 'Paid', 'Due', 'Partial'
    payment_date DATE DEFAULT CURRENT_DATE
);

-- Function to handle updated_at timestamp for student table
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for student table
CREATE TRIGGER update_student_modtime
    BEFORE UPDATE ON student
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
