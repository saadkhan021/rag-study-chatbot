import React, { createContext, useContext, useState, useCallback } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('study_token'))
  const [email, setEmail] = useState(() => localStorage.getItem('study_email'))

  const persist = useCallback((tok, mail) => {
    localStorage.setItem('study_token', tok)
    localStorage.setItem('study_email', mail)
    setToken(tok)
    setEmail(mail)
  }, [])

  const login = useCallback(async (mail, password) => {
    const res = await api.login(mail, password)
    persist(res.access_token, mail)
  }, [persist])

  const signup = useCallback(async (mail, password) => {
    const res = await api.signup(mail, password)
    persist(res.access_token, mail)
  }, [persist])

  const logout = useCallback(() => {
    localStorage.removeItem('study_token')
    localStorage.removeItem('study_email')
    setToken(null)
    setEmail(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, email, login, signup, logout, isAuthed: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
