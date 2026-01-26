from app.core.supabase import supabase
from app.schemas.result import BulkResultRequest
from app.repositories.exam_repository import ExamRepository

class ResultRepository:
    def __init__(self):
        self.result_table = "student_individual_result"
        self.enrollment_table = "enrollment"
        self.exam_repo = ExamRepository()

    def submit_bulk_results(self, bulk_data: BulkResultRequest):
        exam_id = bulk_data.exam_id
        
        # 1. Get the Exam to find the Program ID
        exam = self.exam_repo.get_exam_by_id(exam_id)
        if not exam:
            raise Exception("Exam not found")
        program_id = exam['program_id']

        # 2. Fetch all enrollments for this program to map Student ID -> Enrollment ID
        # We need this because the Result table uses Enrollment ID, but the user (Excel) sends Student ID.
        enrollments = supabase.table(self.enrollment_table)\
            .select("enrollment_id, student_id")\
            .eq("program_id", program_id)\
            .execute().data
        
        # Create a lookup map: { student_id: enrollment_id }
        student_to_enrollment = {e['student_id']: e['enrollment_id'] for e in enrollments}

        # 3. Prepare the data for upsert
        upsert_list = []
        for item in bulk_data.results:
            enrollment_id = student_to_enrollment.get(item.student_id)
            if enrollment_id:
                upsert_list.append({
                    "enrollment_id": enrollment_id,
                    "exam_id": exam_id,
                    "written_marks": item.written_marks,
                    "mcq_marks": item.mcq_marks,
                    # 'total_score' might be auto-calculated by DB generated column, 
                                        # but if Supabase/Postgres version doesn't support it, we send it manually?
                    # The DB schema says GENERATED ALWAYS, so we should NOT send it.
                })

        if not upsert_list:
            return {"message": "No valid enrollments found for provided students"}

        # 4. Perform Bulk Upsert (on_conflict match enrollment_id + exam_id)
        # Note: Supabase upsert requires the primary key or unique constraint columns
        response = supabase.table(self.result_table).upsert(upsert_list, on_conflict="enrollment_id, exam_id").execute()
        return response.data

    def get_exam_results(self, exam_id: int):
        # Fetch results with student details for the Merit List
        response = supabase.table(self.result_table)\
            .select("*, enrollment(student(student_id, name, roll_no))")\
            .eq("exam_id", exam_id)\
            .order("total_score", desc=True)\
            .execute()
        return response.data

    def get_exam_analytics(self, exam_id: int):
        # Get raw results
        results = self.get_exam_results(exam_id)
        if not results:
            return None

        total_students = len(results)
        
        # Calculate Averages and Tops
        # Initialize
        sum_written = 0
        sum_mcq = 0
        sum_total = 0
        max_written = 0
        max_mcq = 0
        max_total = 0

        for r in results:
            w = r.get('written_marks', 0)
            m = r.get('mcq_marks', 0)
            # Calculate total manually to ensure consistency
            t = w + m

            sum_written += w
            sum_mcq += m
            sum_total += t

            if w > max_written: max_written = w
            if m > max_mcq: max_mcq = m
            if t > max_total: max_total = t

        return {
            "total_students": total_students,
            "averages": {
                "written": round(sum_written / total_students, 2),
                "mcq": round(sum_mcq / total_students, 2),
                "total": round(sum_total / total_students, 2)
            },
            "highest": {
                "written": max_written,
                "mcq": max_mcq,
                "total": max_total
            }
        }

    def get_exam_candidates(self, exam_id: int):
        # 1. Get Exam -> Program ID
        exam = self.exam_repo.get_exam_by_id(exam_id)
        if not exam: return []
        program_id = exam['program_id']

        # 2. Get All Enrollments for this Program
        enrollments = supabase.table(self.enrollment_table)\
            .select("*, student(*)")\
            .eq("program_id", program_id)\
            .execute().data
        
        # 3. Get Existing Results for this Exam
        results = supabase.table(self.result_table)\
            .select("*")\
            .eq("exam_id", exam_id)\
            .execute().data
        
        # 4. Merge Data (Left Join Enrollment -> Result)
        # Map result by enrollment_id
        result_map = {r['enrollment_id']: r for r in results}

        candidates = []
        for enroll in enrollments:
            res = result_map.get(enroll['enrollment_id'])
            candidates.append({
                "enrollment_id": enroll['enrollment_id'],
                "student": enroll['student'],
                "result_id": res['result_id'] if res else None,
                "written_marks": res['written_marks'] if res else 0,
                "mcq_marks": res['mcq_marks'] if res else 0,
                "total_score": res['total_score'] if res else 0,
                "has_attended": True if res else False
            })
        
        # Sort by Roll No (Safe access)
        def get_roll(x):
            try:
                return x.get('student', {}).get('roll_no') or 999999
            except:
                return 999999
        
        candidates.sort(key=get_roll)
        return candidates
