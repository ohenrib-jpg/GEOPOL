# Flask/routes_geo_narrative.py - OPTIMISÉ POUR VOTRE PORT 5001
from flask import Blueprint, jsonify, request, Response
import logging

logger = logging.getLogger(__name__)

def create_geo_narrative_blueprint(db_manager, geo_narrative_analyzer):
    bp = Blueprint('geo_narrative', __name__, url_prefix='/api/geo-narrative')

    @bp.route('/patterns', methods=['GET'])
    def get_patterns():
        try:
            days = request.args.get('days', 7, type=int)
            min_countries = request.args.get('min_countries', 2, type=int)

            if days < 1 or days > 90:
                return jsonify({'error': 'days must be 1..90'}), 400
            if min_countries < 2 or min_countries > 10:
                return jsonify({'error': 'min_countries must be 2..10'}), 400

            # Analyse réelle
            try:
                patterns = geo_narrative_analyzer.detect_transnational_patterns(
                    days=days, min_countries=min_countries
                )
                if patterns:
                    logger.info(f"✅ {len(patterns)} patterns réels détectés")
                    return jsonify({
                        'success': True,
                        'source': 'database',
                        'count': len(patterns),
                        'patterns': patterns
                    }), 200
            except Exception as e:
                logger.warning(f"⚠️ Erreur analyse réelle: {e}")

            # Fallback mock enrichi
            mock = [
                {
                    'pattern': 'sanctions économiques contre',
                    'countries': ['FR', 'DE', 'UK', 'US'],
                    'country_count': 4,
                    'total_occurrences': 8,
                    'strength': 4,
                    'entities': {
                        'locations': ['Russie'],
                        'organizations': ['UE', 'OTAN'],
                        'persons': ['Emmanuel Macron', 'Olaf Scholz', 'Joe Biden'],
                        'groups': [],
                        'events': [],
                        'all_entities': ['Russie', 'UE', 'OTAN', 'Emmanuel Macron', 'Olaf Scholz', 'Joe Biden']
                    }
                },
                {
                    'pattern': 'négociations de paix en Ukraine',
                    'countries': ['FR', 'DE', 'UK'],
                    'country_count': 3,
                    'total_occurrences': 5,
                    'strength': 3,
                    'entities': {
                        'locations': ['Ukraine', 'France', 'Allemagne'],
                        'organizations': ['UE', 'OTAN'],
                        'persons': ['Emmanuel Macron', 'Olaf Scholz'],
                        'groups': [],
                        'events': [],
                        'all_entities': ['Ukraine', 'France', 'Allemagne', 'UE', 'OTAN', 'Emmanuel Macron', 'Olaf Scholz']
                    }
                },
                {
                    'pattern': 'coopération militaire',
                    'countries': ['FR', 'DE', 'US'],
                    'country_count': 3,
                    'total_occurrences': 4,
                    'strength': 3,
                    'entities': {
                        'locations': [],
                        'organizations': ['OTAN', 'UE'],
                        'persons': [],
                        'groups': [],
                        'events': [],
                        'all_entities': ['OTAN', 'UE']
                    }
                }
            ]
            
            logger.info("🔧 Utilisation des données mock enrichies")
            return jsonify({
                'success': True,
                'source': 'mock',
                'count': len(mock),
                'patterns': mock
            }), 200

        except Exception as e:
            logger.error(f"❌ /patterns error: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/influence-map', methods=['GET'])
    def get_influence_map():
        try:
            days = request.args.get('days', 7, type=int)
            resp = get_patterns()
            data = resp.get_json()
            patterns = data.get('patterns', [])

            nodes = []
            edges = []

            # Construire les nœuds (pays)
            countries = set()
            for p in patterns:
                countries.update(p.get('countries', []))
            
            country_coords = {
                'FR': [46.2276, 2.2137], 'DE': [51.1657, 10.4515],
                'UK': [55.3781, -3.4360], 'US': [37.0902, -95.7129],
                'ES': [40.4637, -3.7492], 'IT': [41.8719, 12.5674],
                'CN': [35.8617, 104.1954], 'JP': [36.2048, 138.2529],
                'RU': [61.5240, 105.3188]
            }
            
            for c in countries:
                nodes.append({
                    'id': c,
                    'label': c,
                    'x': country_coords.get(c, [0, 0])[1],
                    'y': country_coords.get(c, [0, 0])[0],
                    'size': sum(1 for p in patterns if c in p.get('countries', []))
                })

            # Construire les arêtes (connexions)
            for p in patterns:
                clist = p.get('countries', [])
                for i in range(len(clist)):
                    for j in range(i + 1, len(clist)):
                        edges.append({
                            'source': clist[i],
                            'target': clist[j],
                            'weight': p.get('strength', 1),
                            'label': p.get('pattern', '')[:30]
                        })

            return jsonify({
                'success': True,
                'influence_network': {
                    'nodes': nodes,
                    'edges': edges,
                    'metadata': {
                        'total_patterns': len(patterns),
                        'countries_analyzed': len(countries),
                        'analysis_period': f'{days} jours'
                    }
                }
            }), 200

        except Exception as e:
            logger.error(f"❌ /influence-map error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/map-view', methods=['GET'])
    def map_view():
        html = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Carte Géopolitique - GEOPOL (Port 5001)</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
<style>
  body { margin:0; font-family: 'Segoe UI', Arial, sans-serif; background:#f8fafc; }
  .container { max-width: 1200px; margin: 0 auto; padding: 15px; }
  .header { background:#fff; padding:20px; border-radius:10px; margin-bottom:15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
  .header h1 { color:#2563eb; margin:0; font-size:1.5em; }
  .header p { color:#666; margin:5px 0 0 0; }
  .controls { background:#fff; padding:15px; border-radius:10px; margin-bottom:15px; display:flex; gap:15px; align-items:center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
  #map { height: 500px; width: 100%; border-radius: 10px; border: 2px solid #e5e7eb; }
  .stats { background:#fff; padding:15px; border-radius:10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
  .pattern-item { padding:12px; border-bottom:1px solid #eee; cursor:pointer; background:#fafafa; border-radius:6px; margin-bottom:8px; transition: all 0.3s; }
  .pattern-item:hover { background:#f0f8ff; transform: translateX(3px); }
  .entities { margin-top:8px; font-size:0.9em; color:#666; }
  .entity { background:#e5e7eb; padding:3px 8px; border-radius:12px; margin-right:6px; display:inline-block; margin-bottom:3px; font-size:0.85em; }
  .entities .location { background:#dbeafe; color:#1e40af; }
  .entities .organization { background:#dcfce7; color:#166534; }
  .entities .person { background:#fef3c7; color:#92400e; }
  .entities .group { background:#f3e8ff; color:#7c3aed; }
  .entities .event { background:#fee2e2; color:#dc2626; }
  .loading { text-align:center; padding:30px; color:#2563eb; }
  .source-indicator { margin-left:auto; padding:8px 12px; background:#f3f4f6; border-radius:6px; font-size:0.9em; color:#374151; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🌍 Cartographie Narrative Géopolitique</h1>
    <p>Visualisation des patterns transnationaux et réseaux d'influence (Mode RÉEL)</p>
  </div>
  
  <div class="controls">
    <label>Période (jours): <input type="number" id="days" min="1" max="30" value="7" style="padding:6px; width:70px; margin-left:5px;"></label>
    <label>Pays min: <input type="number" id="min_countries" min="2" max="10" value="2" style="padding:6px; width:70px; margin-left:5px;"></label>
    <button id="reload" style="background:#2563eb; color:white; padding:10px 20px; border:none; border-radius:8px; cursor:pointer; font-weight:600;">🔄 Actualiser</button>
    <div class="source-indicator" id="source-info">Chargement...</div>
  </div>
  
  <div id="map"></div>
  
  <div class="stats">
    <h3 style="color:#2563eb; margin-bottom:15px;">🔍 Patterns Transnationaux Détectés</h3>
    <div id="patterns" class="loading">⏳ Chargement des patterns...</div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
  let map, countryNodes = {};
  const countryCoords = {
    'FR': [46.2276, 2.2137], 'DE': [51.1657, 10.4515], 'UK': [55.3781, -3.4360],
    'US': [37.0902, -95.7129], 'ES': [40.4637, -3.7492], 'IT': [41.8719, 12.5674],
    'CN': [35.8617, 104.1954], 'JP': [36.2048, 138.2529], 'RU': [61.5240, 105.3188]
  };

  function initMap() {
    map = L.map('map').setView([50, 10], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap - GEOPOL Analytics'
    }).addTo(map);
  }

  function clearMap() {
    Object.values(countryNodes).forEach(m => map.removeLayer(m));
    countryNodes = {};
    d3.select('#map').select('svg').remove();
  }

  function updateMap(patterns, source) {
    clearMap();
    document.getElementById('source-info').textContent = `📊 Source: ${source}`;
    
    const counts = {};
    patterns.forEach(p => (p.countries || []).forEach(c => counts[c] = (counts[c] || 0) + 1));

    Object.entries(counts).forEach(([country, count]) => {
      if (countryCoords[country]) {
        const marker = L.circleMarker(countryCoords[country], {
          radius: 8 + (count * 2.5),
          color: '#2563eb',
          fillColor: '#3b82f6',
          fillOpacity: 0.8,
          weight: 2
        }).addTo(map);
        marker.bindPopup(`<b>${country}</b><br/>Patterns: ${count}<br/>Force: ${count}`);
        countryNodes[country] = marker;
      }
    });

    drawInfluenceNetwork(patterns);
  }

  function drawInfluenceNetwork(patterns) {
    const mapContainer = document.getElementById('map');
    const width = mapContainer.clientWidth;
    const height = mapContainer.clientHeight;
    d3.select('#map').select('svg').remove();
    const svg = d3.select('#map').append('svg')
      .attr('width', width).attr('height', height)
      .style('position', 'absolute').style('top', '0').style('left', '0')
      .style('pointer-events', 'none');

    const edges = [];
    patterns.forEach(p => {
      const cs = p.countries || [];
      for (let i = 0; i < cs.length; i++)
        for (let j = i + 1; j < cs.length; j++)
          edges.push({ source: cs[i], target: cs[j], weight: p.strength || 1 });
    });

    edges.forEach(e => {
      const sc = countryCoords[e.source];
      const tc = countryCoords[e.target];
      if (!sc || !tc) return;
      const latlngs = [L.latLng(sc[0], sc[1]), L.latLng(tc[0], tc[1])];
      const projected = latlngs.map(ll => map.latLngToLayerPoint(ll));
      svg.append('line')
        .attr('x1', projected[0].x).attr('y1', projected[0].y)
        .attr('x2', projected[1].x).attr('y2', projected[1].y)
        .attr('stroke', '#10b981').attr('stroke-width', Math.max(2, e.weight))
        .attr('opacity', 0.7);
    });
  }

  function renderPatternsList(patterns) {
    const list = document.getElementById('patterns');
    list.innerHTML = '';
    
    if (patterns.length === 0) {
      list.innerHTML = '<div style="text-align:center; color:#666; padding:20px;">Aucun pattern transnational détecté</div>';
      return;
    }
    
    patterns.slice(0, 25).forEach((p, index) => {
      const el = document.createElement('div');
      el.className = 'pattern-item';
      
      // Construire les entités par catégorie
      const entities = p.entities || {};
      let entitiesHtml = '';
      const allEntities = [
        ...(entities.locations || []).map(e => `<span class="entity location">📍 ${e}</span>`),
        ...(entities.organizations || []).map(e => `<span class="entity organization">🏛️ ${e}</span>`),
        ...(entities.persons || []).map(e => `<span class="entity person">👤 ${e}</span>`),
        ...(entities.groups || []).map(e => `<span class="entity group">👥 ${e}</span>`),
        ...(entities.events || []).map(e => `<span class="entity event">📅 ${e}</span>`)
      ];
      
      if (allEntities.length > 0) {
        entitiesHtml = `<div class="entities"><strong>Entités détectées:</strong> ${allEntities.join(' ')}</div>`;
      }
      
      el.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div style="flex:1;">
            <div style="font-weight:bold; color:#1f2937; margin-bottom:6px; font-size:1.1em;">"${p.pattern}"</div>
            <div style="font-size:0.95em; color:#6b7280; margin-bottom:6px;">🌍 ${(p.countries || []).join(', ')} | 💪 Force: ${p.strength} | 📊 Pays: ${p.country_count}</div>
            ${entitiesHtml}
          </div>
          <div style="background:#2563eb; color:white; padding:8px 12px; border-radius:8px; font-size:0.9em; min-width:60px; text-align:center; margin-left:15px;">
            ${p.total_occurrences}
          </div>
        </div>
      `;
      
      list.appendChild(el);
    });
  }

  async function loadData() {
    const days = document.getElementById('days').value;
    const min_countries = document.getElementById('min_countries').value;

    document.getElementById('patterns').innerHTML = '<div class="loading">⏳ Analyse en cours...</div>';

    try {
      const response = await fetch(`/api/geo-narrative/patterns?days=${days}&min_countries=${min_countries}`);
      const data = await response.json();
      const patterns = data.patterns || [];
      updateMap(patterns, data.source || 'inconnue');
      renderPatternsList(patterns);
    } catch (e) {
      console.error('Erreur API, fallback mock', e);
      const mock = [
        {
          pattern: 'sanctions économiques contre',
          countries: ['FR','DE','UK','US'],
          strength: 4,
          entities: {
            locations: ['Russie'],
            organizations: ['UE', 'OTAN'],
            persons: ['Emmanuel Macron', 'Olaf Scholz', 'Joe Biden'],
            groups: [],
            events: [],
            all_entities: ['Russie', 'UE', 'OTAN', 'Emmanuel Macron', 'Olaf Scholz', 'Joe Biden']
          }
        },
        {
          pattern: 'négociations de paix en Ukraine',
          countries: ['FR','DE','UK'],
          strength: 3,
          entities: {
            locations: ['Ukraine', 'France', 'Allemagne'],
            organizations: ['UE', 'OTAN'],
            persons: ['Emmanuel Macron', 'Olaf Scholz'],
            groups: [],
            events: [],
            all_entities: ['Ukraine', 'France', 'Allemagne', 'UE', 'OTAN', 'Emmanuel Macron', 'Olaf Scholz']
          }
        }
      ];
      updateMap(mock, 'mock');
      renderPatternsList(mock);
    }
  }

  document.getElementById('reload').addEventListener('click', loadData);
  document.addEventListener('DOMContentLoaded', function () {
    initMap();
    loadData();
  });
</script>
</body>
</html>
        """
        return Response(html, mimetype='text/html')

    @bp.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'geo_narrative_operational'}), 200

    logger.info("✅ Blueprint geo_narrative opérationnel créé")
    return bp

def register_geo_narrative_routes(app, db_manager, geo_narrative_analyzer):
    try:
        bp = create_geo_narrative_blueprint(db_manager, geo_narrative_analyzer)
        app.register_blueprint(bp)
        logger.info("✅ Routes geo_narrative opérationnelles enregistrées")
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement geo_narrative: {e}")
        raise
