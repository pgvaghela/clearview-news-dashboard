import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import StoryPage from './pages/StoryPage.jsx'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/story/:id" element={<StoryPage />} />
      </Routes>
    </div>
  )
}
