import { useApi } from '../hooks/useApi.js'
import { fetchFactChecks } from '../services/api.js'
import FactCheckPanel from './FactCheckPanel.jsx'
import WebcitePanel from './WebcitePanel.jsx'

/**
 * Single fetch for /factchecks; renders Google fact-checks and WebCite as separate panels.
 */
export default function StoryFactSources({ storyId }) {
  const { data, loading, error } = useApi(
    () => fetchFactChecks(storyId),
    [storyId]
  )

  return (
    <>
      <FactCheckPanel data={data} loading={loading} error={error} />
      <WebcitePanel webcite={data?.webcite} loading={loading} error={error} />
    </>
  )
}
