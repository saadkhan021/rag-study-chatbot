const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function getToken() {
  return localStorage.getItem('study_token')
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // Non-JSON body — shouldn't happen after the backend's exception
    // handler fix, but don't crash the UI if it does.
  }

  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || `Request failed (${res.status})`
    throw new Error(detail)
  }
  return data
}

export const api = {
  signup: (email, password) => request('/auth/signup', { method: 'POST', body: { email, password }, auth: false }),
  login: (email, password) => request('/auth/login', { method: 'POST', body: { email, password }, auth: false }),

  listAvailableCourses: () => request('/courses', { auth: false }),
  myCourses: () => request('/me/courses'),
  addCourse: (course_name) => request('/me/courses', { method: 'POST', body: { course_name } }),
  removeCourse: (course_name) => request(`/me/courses/${encodeURIComponent(course_name)}`, { method: 'DELETE' }),

  getMessages: (course_name) => request(`/conversations/${encodeURIComponent(course_name)}/messages`),
  sendMessage: (course_name, content) =>
    request(`/conversations/${encodeURIComponent(course_name)}/messages`, { method: 'POST', body: { content } }),

  rateMessage: (message_id, rating, note) =>
    request(`/messages/${message_id}/feedback`, { method: 'POST', body: { rating, note } }),
  regenerateMessage: (message_id, note) =>
    request(`/messages/${message_id}/regenerate`, { method: 'POST', body: { note } }),

  momentum: () => request('/me/momentum'),

  weakTopics: (course_name) => request(`/me/progress/${encodeURIComponent(course_name)}/weak`),
  courseProgress: (course_name) => request(`/me/progress/${encodeURIComponent(course_name)}`),
  studyPlan: (course_name) => request(`/me/plan/${encodeURIComponent(course_name)}`),

  generateQuiz: (course_name, count = 5) =>
    request(`/exam/${encodeURIComponent(course_name)}/quiz?count=${count}`, { method: 'POST' }),
  gradeAnswer: (course_name, question_id, question, topic, answer) =>
    request(`/exam/${encodeURIComponent(course_name)}/grade`, {
      method: 'POST',
      body: { question_id, question, topic, answer },
    }),
}

export { getToken }
