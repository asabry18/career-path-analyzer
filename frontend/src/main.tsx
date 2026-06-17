import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import { AuthProvider } from './context/AuthProvider'
import { AnalysisProvider } from './context/AnalysisContext'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage/index'
import SkillsPage from './pages/SkillsPage/index'
import PrioritiesPage from './pages/PrioritiesPage/index'
import RecommendationsPage from './pages/RecommendationsPage/index'
import ProfilePage from './pages/ProfilePage/index'
import LoginPage from './pages/LoginPage/index'
import SignupPage from './pages/SignupPage/index'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AnalysisProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skills"
              element={
                <ProtectedRoute>
                  <SkillsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/priorities"
              element={
                <ProtectedRoute>
                  <PrioritiesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recommendations"
              element={
                <ProtectedRoute>
                  <RecommendationsPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AnalysisProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
