import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Auth from './pages/Auth'
import CourseSelect from './pages/CourseSelect'
import Dashboard from './pages/Dashboard'

function RequireAuth({ children }) {
  const { isAuthed } = useAuth()
  return isAuthed ? children : <Navigate to="/" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Auth />} />
      <Route
        path="/courses"
        element={
          <RequireAuth>
            <CourseSelect />
          </RequireAuth>
        }
      />
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/dashboard/:courseName"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
