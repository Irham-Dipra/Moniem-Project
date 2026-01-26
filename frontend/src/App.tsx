import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Programs from './pages/Programs';
import StudentList from './components/StudentList';
import StudentProfile from './pages/StudentProfile';
import ProgramDetails from './pages/ProgramDetails';
import ExamDetails from './pages/ExamDetails';
import Exams from './pages/Exams';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* The Layout component wraps all these routes */}
        <Route element={<Layout />}>

          {/* Default Path: Redirect to Dashboard */}
          <Route path="/" element={<Dashboard />} />

          {/* Modules */}
          <Route path="/programs" element={<Programs />} />
          <Route path="/programs/:id" element={<ProgramDetails />} />

          {/* Exams Route */}
          <Route path="/exams" element={<Exams />} />
          <Route path="/exams/:id" element={<ExamDetails />} />

          <Route path="/students" element={<StudentList />} />
          <Route path="/students/:id" element={<StudentProfile />} />

          {/* Catch-all: Redirect to Home */}
          <Route path="*" element={<Navigate to="/" replace />} />

        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;