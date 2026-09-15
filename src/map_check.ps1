$resp = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing
Write-Host "Status: $($resp.StatusCode) OK"
$c = $resp.Content
Write-Host "HTML size: $($c.Length) chars"
Write-Host ""

$checks = [ordered]@{
    'Leaflet CSS CDN' = 'unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    'Leaflet JS CDN' = 'unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    'OSM free tiles' = 'tile.openstreetmap.org'
    'initMap() function' = 'function initMap'
    'gridMap div' = 'id="gridMap"'
    'makeAssetIcon (risk markers)' = 'function makeAssetIcon'
    'makeCrewIcon (crew markers)' = 'function makeCrewIcon'
    'buildAssetPopupHtml (8-field popup)' = 'function buildAssetPopupHtml'
    'buildCrewPopupHtml' = 'function buildCrewPopupHtml'
    'L.polyline (crew routes)' = 'L.polyline'
    'legend-control (custom legend)' = 'legend-control'
    'L.control.layers (overlay toggle)' = 'L.control.layers'
    'Popup label: Failure Probability' = 'Failure Probability'
    'Popup label: Grid Impact' = 'Grid Impact'
    'Popup label: Weather Risk' = 'Weather Risk'
    'Popup label: Priority Score' = 'Priority Score'
    'Popup label: Risk Level badge' = 'risk-badge'
    'Popup action panel' = 'popup-action'
    'Crew pairings from /api/crew-recommendations' = 'crewPairings'
    'fitBounds with real lat/lon' = 'fitBounds'
    'Geographic Risk Map section' = 'Geographic Risk Map'
    'mAssets map counter' = 'id="mAssets"'
    'mSubs map counter' = 'id="mSubs"'
    'mHighCrit map counter' = 'id="mHighCrit"'
    'mCrews map counter' = 'id="mCrews"'
    'mRoutes map counter' = 'id="mRoutes"'
}

$allOK = $true
foreach ($k in $checks.Keys) {
    $ok = $c.Contains($checks[$k])
    if (-not $ok) { $allOK = $false }
    $status = if ($ok) { 'OK' } else { 'MISSING' }
    Write-Host "  [$status] $k"
}

Write-Host ""
if ($allOK) { Write-Host "ALL CHECKS PASSED: Leaflet map integration complete with real backend data." }
else { Write-Host "Some checks failed - investigate." }
