const BASE = '/api/v1'

export async function fetchStories(page = 1, pageSize = 15) {
  const res = await fetch(`${BASE}/stories?page=${page}&page_size=${pageSize}`)
  if (!res.ok) throw new Error(`Failed to fetch stories: ${res.status}`)
  return res.json()
}

export async function fetchStory(id) {
  const res = await fetch(`${BASE}/stories/${id}`)
  if (!res.ok) throw new Error(`Story not found: ${res.status}`)
  return res.json()
}

export async function fetchFactChecks(id) {
  const res = await fetch(`${BASE}/stories/${id}/factchecks`)
  if (!res.ok) throw new Error(`Failed to fetch fact checks: ${res.status}`)
  return res.json()
}
