import StudentList from './components/StudentList'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      <header className="w-full bg-blue-600 text-white p-6 shadow-md mb-8">
        <h1 className="text-3xl font-bold text-center">Coaching Management Admin</h1>
      </header>
      
      <main className="w-full max-w-4xl">
        <StudentList />
      </main>
    </div>
  )
}

export default App