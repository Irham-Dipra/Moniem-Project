from app.core.supabase import supabase
from datetime import datetime, date

class PaymentRepository:
    """
    Repository class for handling all database operations related to Payments.
    It uses Supabase (a backend-as-a-service wrapping PostgreSQL) to store and retrieve data.
    """
    def __init__(self):
        # define the table names we will be working with
        self.table = "payment"
        self.enrollment_table = "enrollment"

    def create_payment(self, data: dict):
        """
        Creates a new payment record.
        
        Algorithm:
        1. Find the `enrollment_id` for the given student and program.
           - We need this because payments are linked to an 'Enrollment', not just a raw student.
           - This ensures we know exactly WHICH program they are paying for.
        2. Construct the payment data object (amount, date, month, year, etc.).
        3. Insert into the `payment` table.
        """
        print(f"Resolving enrollment for Student {data['student_id']} Program {data['program_id']}")
        
        # Step 1: Query the 'enrollment' table
        # We look for a row where student_id AND program_id match the input.
        # SQL Equiv: SELECT enrollment_id FROM enrollment WHERE student_id = ? AND program_id = ?
        enrollment = supabase.table(self.enrollment_table)\
            .select("enrollment_id")\
            .eq("student_id", data['student_id'])\
            .eq("program_id", data['program_id'])\
            .execute().data
            
        print(f"Enrollment found: {enrollment}")
        
        # Validation: If they aren't enrolled, we can't accept payment for this program.
        if not enrollment:
            raise Exception(f"Enrollment not found for Student ID {data['student_id']} in Program ID {data['program_id']}")
            
        # Extract the ID from the result list (enrollment will be a list like [{'enrollment_id': 123}])
        enrollment_id = enrollment[0]['enrollment_id']
        
        try:
            # Step 2: Prepare the data dictionary for Supabase
            payment_data = {
                "enrollment_id": enrollment_id,
                "paid_amount": float(data['paid_amount']),   # Ensure amount is a number
                "payment_date": data['payment_date'],        # Strings like "2024-01-27" work for Date types
                "month": int(data.get('month')),             # Month they are paying for (1-12)
                "year": int(data.get('year')),               # Year they are paying for
                "payment_method": data.get('payment_method'),# Cash, bKash, etc.
                "remarks": data.get('remarks'),              # Optional notes
                "status": 'Paid'                             # Default status
            }
            # print(f"Inserting Payment Data: {payment_data}")
            
            # Step 3: Insert into the database
            response = supabase.table(self.table).insert(payment_data).execute()
            # print(f"Insert Response: {response}")
            
            # Return the created record
            return response.data[0]
        except Exception as e:
            print(f"Error inserting payment: {e}")
            raise e

    def get_recent_payments(self, limit: int = 50):
        """
        Fetches the latest payments for the global transaction ledger.
        
        Algorithm:
        1. Select all columns (*) from payment.
        2. JOIN with enrollment table to get student and program details.
           - Syntax: enrollment(student(name, roll_no), program(program_name))
           - This is Supabase's powerful nested join syntax. It goes Payment -> Enrollment -> Student/Program.
        3. Order by date descending (newest first).
        4. Flatten the nested structure for easier use in the frontend.
        """
        # Step 1 & 2: Query with Joins
        response = supabase.table(self.table)\
            .select("*, enrollment(student(name, roll_no), program(program_name))")\
            .order("payment_date", desc=True)\
            .limit(limit)\
            .execute()
            
        result = []
        # Step 4: Transform/Flatten Data
        # The raw data looks like: { "paid_amount": 500, "enrollment": { "student": { "name": "John" } } }
        # We want: { "paid_amount": 500, "student_name": "John" }
        for r in response.data:
            enroll = r.get('enrollment') or {}
            student = enroll.get('student') or {}
            program = enroll.get('program') or {}
            
            result.append({
                **r,
                "student_name": student.get("name"),
                "roll_no": student.get("roll_no"),
                "program_name": program.get("program_name")
            })
        return result

    def get_student_payments(self, student_id: int):
        """
        Fetches payment history for a specific student.
        
        Algorithm:
        1. Find all `enrollment_ids` belonging to this student.
        2. Create a map of ID -> Program Name so we can label payments later.
        3. Query the `payment` table for ALL payments that match ANY of these enrollment IDs (using '.in_').
        4. Attach the program name to each payment record.
        """
        # Step 1: Get Enrollments
        enrollments = supabase.table(self.enrollment_table)\
            .select("enrollment_id, program(program_name)")\
            .eq("student_id", student_id)\
            .execute().data
            
        if not enrollments:
            return []
            
        # Extract IDs list: [1, 5, 8]
        enrollment_ids = [e['enrollment_id'] for e in enrollments]
        # Create Helper Map: {1: "English", 5: "Math"}
        program_map = {e['enrollment_id']: e['program']['program_name'] for e in enrollments if e.get('program')}
        
        # Step 3: Fetch Payments for these enrollments
        response = supabase.table(self.table)\
            .select("*")\
            .in_("enrollment_id", enrollment_ids)\
            .order("payment_date", desc=True)\
            .execute()
            
        result = []
        for r in response.data:
            # Step 4: Attach Program Name
            result.append({
                **r,
                "program_name": program_map.get(r['enrollment_id'], "Unknown Program")
            })
        return result

    def get_finance_stats(self):
        """
        Calculates financial dashboards stats: Total Revenue and Total Due.
        This is the most complex function logic-wise.
        
        Algorithm:
        1. Fetch ALL payments (lightweight query, just amounts and dates).
        2. Fetch ALL active enrollments (to know who SHOULD be paying).
        3. Calculate Revenue:
           - Sum of checks/cash collected. Simple addition.
        4. Calculate Due (The tricky part):
           - Can't just check if (Fee * Months) > Paid, because one student might have overpaid 
             and another underpaid. We can't let Student A's surplus hide Student B's debt.
           - We must iterate STUDENT BY STUDENT.
           - For each student:
             a. Calculate expected fee (Months since joining * Monthly Fee).
             b. Sum their total payments.
             c. If Expected > Paid, the difference is their DUE.
             d. If Paid > Expected, their Due is 0 (they are in advance).
           - Sum up all the individual "Dues" to get the Total Arrears.
        5. Calculate 'Due This Month':
           - The amount specifically expected for the current calendar month that hasn't been paid precisely for this month.
        """
        # Step 1: Fetch Raw Payment Data
        # We need 'month' and 'year' to check specific monthly dues
        all_payments = supabase.table(self.table).select("enrollment_id, paid_amount, payment_date, month, year").execute().data
        
        # Step 2: Fetch Active Enrollments
        # We only care about 'Active' students for calculating current dues.
        enrollments = supabase.table(self.enrollment_table)\
            .select("enrollment_id, enrollment_date, status, program(monthly_fee)")\
            .eq("status", "Active")\
            .execute().data

        # --- REVENUE CALCULATION ---
        # Total Cash in hand (All time)
        total_revenue = sum(p['paid_amount'] for p in all_payments)
        
        today = date.today()
        # Revenue This Month: Sum of payments made in the current calendar month (by payment_date)
        revenue_this_month = sum(p['paid_amount'] for p in all_payments if p['payment_date'].startswith(f"{today.year}-{today.month:02d}"))

        # --- DUE CALCULATION ---
        total_due_overall = 0
        total_due_this_month = 0
        
        # Optimization: Group payments by enrollment_id dictionary for O(1) lookup inside the loop
        # Format: { 101: [PaymentA, PaymentB], 102: [PaymentC] }
        payments_by_enrollment = {}
        for p in all_payments:
            eid = p['enrollment_id']
            if eid not in payments_by_enrollment:
                payments_by_enrollment[eid] = []
            payments_by_enrollment[eid].append(p)

        # Iterate through every single student (enrollment)
        for env in enrollments:
            prog = env.get('program')
            if not prog or not env['enrollment_date']: continue
            
            fee = float(prog['monthly_fee'] or 0)
            if fee == 0: continue
            
            # Get this specific student's payment history
            student_payments = payments_by_enrollment.get(env['enrollment_id'], [])
            
            # A. Calculate Total Arrears (Lifetime Due)
            # How many months have they been here?
            start = datetime.strptime(env['enrollment_date'], "%Y-%m-%d").date()
            months_passed = (today.year - start.year) * 12 + (today.month - start.month) + 1
            months_passed = max(0, months_passed)
            
            expected_lifetime = months_passed * fee
            paid_lifetime = sum(p['paid_amount'] for p in student_payments)
            
            # IMPORTANT: max(0, ...) ensures we don't count negative due (advance payment)
            student_due_total = max(0, expected_lifetime - paid_lifetime)
            
            # Add to the global accumulator
            total_due_overall += student_due_total
            
            # B. Calculate Due This Specific Month
            # Logic: Fee - (Sum of payments tagged specifically for THIS month/year)
            if start <= today:
                fee_this_month = fee
                # Filter payments that have month=CurrentMonth AND year=CurrentYear
                paid_for_this_month = sum(p['paid_amount'] for p in student_payments if p.get('month') == today.month and p.get('year') == today.year)
                
                student_due_this_month = max(0, fee_this_month - paid_for_this_month)
                total_due_this_month += student_due_this_month
        
        return {
            "total_revenue": total_revenue,
            "revenue_this_month": revenue_this_month,
            "due_total": total_due_overall,
            "due_this_month": total_due_this_month
        }

    def get_program_finance_stats(self):
        """
        Aggregates financial data by Program (e.g. "Physics Batch A" has collected X amount).
        Used for reports.
        """
        # Return list of programs with their financial breakdown
        programs = supabase.table("program").select("program_id, program_name, monthly_fee, batch(batch_name)").execute().data
        enrollments = supabase.table(self.enrollment_table).select("enrollment_id, program_id").execute().data
        all_payments = supabase.table(self.table).select("enrollment_id, paid_amount, payment_date").execute().data
        
        stats = []
        today = date.today()
        
        for prog in programs:
            pid = prog['program_id']
            # Find all students enrolled in this program
            prog_enrollments = [e['enrollment_id'] for e in enrollments if e['program_id'] == pid]
            
            # Find all payments linked to these enrollments
            prog_payments = [p for p in all_payments if p['enrollment_id'] in prog_enrollments]
            
            revenue_overall = sum(p['paid_amount'] for p in prog_payments)
            revenue_this_month = sum(p['paid_amount'] for p in prog_payments if p['payment_date'].startswith(f"{today.year}-{today.month:02d}"))
            
            stats.append({
                "program_id": pid,
                "program_name": f"{prog['program_name']} ({prog.get('batch', {}).get('batch_name')})",
                "total_revenue": revenue_overall,
                "revenue_this_month": revenue_this_month,
                "active_students": len(prog_enrollments)
            })
            
        return stats
