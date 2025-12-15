# Flask/weak_indicators/routes.py
"""Routes du module Weak Indicators"""

from flask import Blueprint, jsonify, render_template, request, Response, make_response
import logging
from datetime import datetime
import csv
import io
import json

logger = logging.getLogger(__name__)

def create_weak_indicators_blueprint(service):
    """Crée le blueprint des Weak Indicators"""
    
    weak_bp = Blueprint('weak_indicators', __name__, 
                       template_folder='templates',
                       static_folder='static',
                       url_prefix='/weak-indicators')
    
    @weak_bp.route('/')
    def dashboard():
        """Page principale du dashboard"""
        return render_template('weak_indicators.html')
    
    @weak_bp.route('/api/dashboard')
    async def get_dashboard():
        """API pour les données du dashboard"""
        try:
            data = await service.get_dashboard_data()
            
            return jsonify({
                'success': True,
                'data': {
                    'travel': [adv.__dict__ for adv in data.travel_advisories],
                    'financial': [inst.__dict__ for inst in data.financial_data],
                    'sdr': [act.__dict__ for act in data.sdr_activities]
                },
                'timestamp': data.timestamp.isoformat(),
                'source': 'database'
            })
        except Exception as e:
            logger.error(f"Erreur API dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @weak_bp.route('/api/travel')
    def get_travel_advisories():
        """API pour les avis de voyage"""
        try:
            data = service._get_travel_advisories_db()
            return jsonify({
                'success': True,
                'data': [adv.__dict__ for adv in data],
                'count': len(data),
                'source': 'database'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @weak_bp.route('/api/financial')
    def get_financial_data():
        """API pour les données financières"""
        try:
            data = service._get_financial_data_db()
            return jsonify({
                'success': True,
                'data': [inst.__dict__ for inst in data],
                'count': len(data),
                'source': 'database'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @weak_bp.route('/api/stats')
    def get_stats():
        """API pour les statistiques"""
        try:
            scraping_stats = service.get_scraping_stats()
            
            return jsonify({
                'success': True,
                'stats': {
                    'scraping': scraping_stats,
                    'cache': {
                        'travel': 'active' if service.cache.get('travel_advisories') else 'inactive',
                        'financial': 'active' if service.cache.get('financial_data') else 'inactive'
                    }
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @weak_bp.route('/api/force-update', methods=['POST'])
    def force_update():
        """Force la mise à jour des données"""
        try:
            service.update_all_data()
            return jsonify({
                'success': True,
                'message': 'Mise à jour déclenchée'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @weak_bp.route('/api/export/<data_type>')
    def export_data(data_type):
        """Exporte les données en CSV"""
        try:
            if data_type == 'travel':
                data = service._get_travel_advisories_db()
                return export_travel_csv(data)
            elif data_type == 'financial':
                data = service._get_financial_data_db()
                return export_financial_csv(data)
            elif data_type == 'sdr':
                data = service._get_sdr_activities_db()
                return export_sdr_csv(data)
            elif data_type == 'all':
                return export_all_data(service)
            else:
                return jsonify({
                    'success': False,
                    'error': f'Type de données inconnu: {data_type}'
                }), 400
                
        except Exception as e:
            logger.error(f"Erreur export {data_type}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def export_travel_csv(advisories):
        """Exporte les avis de voyage en CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-tête avec encodage UTF-8 et séparateur point-virgule pour Excel français
        writer.writerow([
            'Code Pays', 'Pays', 'Niveau Risque', 
            'Description Risque', 'Source', 'Résumé',
            'Dernière Mise à Jour', 'URL Source'
        ])
        
        for adv in advisories:
            risk_description = {
                1: 'Précautions normales',
                2: 'Prudence accrue', 
                3: 'Réenvisager le voyage',
                4: 'Ne pas voyager'
            }.get(adv.risk_level, 'Inconnu')
            
            writer.writerow([
                adv.country_code,
                adv.country_name,
                adv.risk_level,
                risk_description,
                adv.source,
                (adv.summary or '')[:200],  # Limiter la longueur
                adv.last_updated.strftime('%Y-%m-%d %H:%M:%S') if hasattr(adv.last_updated, 'strftime') else str(adv.last_updated),
                adv.raw_data.get('url', '') if adv.raw_data else ''
            ])
        
        # Préparer la réponse
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'  # UTF-8 avec BOM pour Excel
        response.headers['Content-Disposition'] = f'attachment; filename=geopol_travel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    
    def export_financial_csv(instruments):
        """Exporte les données financières en CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Symbole', 'Nom', 'Prix Actuel', 'Variation %',
            'Volume', 'Catégorie', 'Source', 'Horodatage'
        ])
        
        for inst in instruments:
            writer.writerow([
                inst.symbol,
                inst.name,
                f"{inst.current_price:.2f}",
                f"{inst.change_percent:+.2f}%",
                f"{inst.volume:,}" if inst.volume else 'N/A',
                inst.category,
                inst.source,
                inst.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(inst.timestamp, 'strftime') else str(inst.timestamp)
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=geopol_financial_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    
    def export_sdr_csv(activities):
        """Exporte les activités SDR en CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Fréquence (kHz)', 'Nom', 'Compteur Activité',
            'Intensité (%)', 'Anomalie', 'Dernière Détection',
            'Source', 'Catégorie'
        ])
        
        # Fonction helper pour catégoriser les fréquences
        def categorize_frequency(freq):
            """Catégorise une fréquence"""
            if freq < 3000:
                return 'VLF/LF'
            elif freq < 30000:
                return 'HF'
            elif freq < 300000:
                return 'VHF'
            else:
                return 'UHF+'
        
        for act in activities:
            intensity = min(100, max(0, act.activity_count))
            
            writer.writerow([
                act.frequency_khz,
                act.name,
                act.activity_count,
                f"{intensity}%",
                'OUI' if act.is_anomaly else 'NON',
                act.last_seen.strftime('%Y-%m-%d %H:%M:%S') if hasattr(act.last_seen, 'strftime') else str(act.last_seen),
                act.source,
                categorize_frequency(act.frequency_khz)  # Appel corrigé
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=geopol_sdr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    
    def export_all_data(service):
        """Exporte toutes les données dans un ZIP ou JSON"""
        try:
            all_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'system': 'GEOPOL Analytics',
                    'version': '1.0'
                },
                'travel_advisories': [adv.__dict__ for adv in service._get_travel_advisories_db()],
                'financial_instruments': [inst.__dict__ for inst in service._get_financial_data_db()],
                'sdr_activities': [act.__dict__ for act in service._get_sdr_activities_db()]
            }
            
            # Nettoyer les objets datetime pour JSON
            for category in ['travel_advisories', 'financial_instruments', 'sdr_activities']:
                for item in all_data[category]:
                    for key, value in item.items():
                        if hasattr(value, 'isoformat'):
                            item[key] = value.isoformat()
            
            json_output = json.dumps(all_data, ensure_ascii=False, indent=2)
            
            response = make_response(json_output)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=geopol_complete_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur export complet: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def _categorize_frequency(freq):
        """Catégorise une fréquence"""
        if freq < 3000:
            return 'VLF/LF'
        elif freq < 30000:
            return 'HF'
        elif freq < 300000:
            return 'VHF'
        else:
            return 'UHF+'
    
    @weak_bp.route('/api/export/formats')
    def get_export_formats():
        """Retourne les formats d'export disponibles"""
        return jsonify({
            'success': True,
            'formats': [
                {'id': 'travel', 'name': 'Avis de Voyage', 'format': 'CSV'},
                {'id': 'financial', 'name': 'Données Financières', 'format': 'CSV'},
                {'id': 'sdr', 'name': 'Activités SDR', 'format': 'CSV'},
                {'id': 'all', 'name': 'Toutes les données', 'format': 'JSON'}
            ]
        })

    @weak_bp.route('/api/clear-cache', methods=['POST'])
    def clear_cache():
        """Nettoie le cache"""
        try:
            service.cache._cache.clear()
            service.cache._timestamps.clear()
            
            return jsonify({
                'success': True,
                'message': 'Cache nettoyé',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    

    @weak_bp.route('/api/filtered-data')
    def get_filtered_data():
        """Retourne les données filtrées selon les critères"""
        try:
            # Récupérer les paramètres de filtrage
            filters = request.args.to_dict()
            
            # Récupérer toutes les données
            travel_data = service._get_travel_advisories_db()
            financial_data = service._get_financial_data_db()
            sdr_data = service._get_sdr_activities_db()
            
            # Appliquer les filtres
            filtered_travel = apply_travel_filters(travel_data, filters)
            filtered_financial = apply_financial_filters(financial_data, filters)
            filtered_sdr = apply_sdr_filters(sdr_data, filters)
            
            return jsonify({
                'success': True,
                'data': {
                    'travel': [adv.__dict__ for adv in filtered_travel],
                    'financial': [inst.__dict__ for inst in filtered_financial],
                    'sdr': [act.__dict__ for act in filtered_sdr]
                },
                'counts': {
                    'travel': len(filtered_travel),
                    'financial': len(filtered_financial),
                    'sdr': len(filtered_sdr),
                    'total': len(filtered_travel) + len(filtered_financial) + len(filtered_sdr)
                },
                'filters_applied': filters
            })
            
        except Exception as e:
            logger.error(f"Erreur filtrage: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    def apply_travel_filters(advisories, filters):
        """Applique les filtres aux avis de voyage"""
        filtered = advisories
    
        # Filtre par niveau de risque
        if 'min_risk' in filters:
            min_risk = int(filters['min_risk'])
            filtered = [a for a in filtered if a.risk_level >= min_risk]
    
        if 'max_risk' in filters:
            max_risk = int(filters['max_risk'])
            filtered = [a for a in filtered if a.risk_level <= max_risk]
    
        # Filtre par source
        if 'sources' in filters:
            sources = filters['sources'].split(',')
            filtered = [a for a in filtered if a.source in sources]
    
        # Filtre par pays
        if 'countries' in filters:
            countries = filters['countries'].split(',')
            filtered = [a for a in filtered if a.country_code in countries or a.country_name in countries]
    
        # Filtre par recherche textuelle
        if 'search' in filters and filters['search']:
            search_term = filters['search'].lower()
            filtered = [a for a in filtered if 
                   search_term in a.country_name.lower() or 
                   (a.summary and search_term in a.summary.lower())]
    
        # Tri
        sort_by = filters.get('sort', 'risk_desc')
        if sort_by == 'risk_desc':
            filtered.sort(key=lambda x: x.risk_level, reverse=True)
        elif sort_by == 'risk_asc':
            filtered.sort(key=lambda x: x.risk_level)
        elif sort_by == 'name_asc':
            filtered.sort(key=lambda x: x.country_name)
        elif sort_by == 'date_desc':
            filtered.sort(key=lambda x: x.last_updated, reverse=True)
    
        # Limite
        limit = int(filters.get('limit', 50))
        return filtered[:limit]

    def apply_financial_filters(instruments, filters):
        """Applique les filtres aux données financières"""
        filtered = instruments
    
        # Filtre par catégorie
        if 'categories' in filters:
            categories = filters['categories'].split(',')
            filtered = [i for i in filtered if i.category in categories]
    
        # Filtre par variation
        if 'min_change' in filters:
            min_change = float(filters['min_change'])
            filtered = [i for i in filtered if i.change_percent >= min_change]
    
        if 'max_change' in filters:
            max_change = float(filters['max_change'])
            filtered = [i for i in filtered if i.change_percent <= max_change]
    
        # Tri
        sort_by = filters.get('sort', 'change_desc')
        if sort_by == 'change_desc':
            filtered.sort(key=lambda x: x.change_percent, reverse=True)
        elif sort_by == 'change_asc':
            filtered.sort(key=lambda x: x.change_percent)
        elif sort_by == 'name_asc':
            filtered.sort(key=lambda x: x.name)
        elif sort_by == 'price_desc':
            filtered.sort(key=lambda x: x.current_price, reverse=True)
    
        return filtered

    def apply_sdr_filters(activities, filters):
        """Applique les filtres aux activités SDR"""
        filtered = activities
    
        # Filtre par anomalie
        if 'anomaly_only' in filters and filters['anomaly_only'].lower() == 'true':
            filtered = [a for a in filtered if a.is_anomaly]
    
        # Filtre par fréquence
        if 'min_freq' in filters:
            min_freq = int(filters['min_freq'])
            filtered = [a for a in filtered if a.frequency_khz >= min_freq]
    
        if 'max_freq' in filters:
            max_freq = int(filters['max_freq'])
            filtered = [a for a in filtered if a.frequency_khz <= max_freq]
    
        # Tri
        sort_by = filters.get('sort', 'activity_desc')
        if sort_by == 'activity_desc':
            filtered.sort(key=lambda x: x.activity_count, reverse=True)
        elif sort_by == 'freq_asc':
            filtered.sort(key=lambda x: x.frequency_khz)
        elif sort_by == 'freq_desc':
            filtered.sort(key=lambda x: x.frequency_khz, reverse=True)
    
        return filtered

    @weak_bp.route('/api/available-filters')
    def get_available_filters():
        """Retourne les options de filtrage disponibles"""
        try:
            travel_data = service._get_travel_advisories_db()
            financial_data = service._get_financial_data_db()
        
            # Extraire les options uniques
            sources = sorted(list(set([a.source for a in travel_data])))
            countries = sorted(list(set([a.country_name for a in travel_data])))
            categories = sorted(list(set([i.category for i in financial_data])))
        
            return jsonify({
                'success': True,
                'filters': {
                    'travel': {
                        'risk_levels': [
                            {'value': 1, 'label': 'Précautions normales', 'color': 'green'},
                            {'value': 2, 'label': 'Prudence accrue', 'color': 'yellow'},
                            {'value': 3, 'label': 'Réenvisager le voyage', 'color': 'orange'},
                            {'value': 4, 'label': 'Ne pas voyager', 'color': 'red'}
                        ],
                        'sources': sources,
                        'countries': countries,
                        'sort_options': [
                            {'value': 'risk_desc', 'label': 'Risque (haut → bas)'},
                            {'value': 'risk_asc', 'label': 'Risque (bas → haut)'},
                            {'value': 'name_asc', 'label': 'Pays (A → Z)'},
                            {'value': 'date_desc', 'label': 'Date (récent → ancien)'}
                        ]
                    },
                    'financial': {
                        'categories': categories,
                        'sort_options': [
                            {'value': 'change_desc', 'label': 'Variation (↑ → ↓)'},
                            {'value': 'change_asc', 'label': 'Variation (↓ → ↑)'},
                            {'value': 'name_asc', 'label': 'Nom (A → Z)'},
                            {'value': 'price_desc', 'label': 'Prix (haut → bas)'}
                        ]
                    },
                    'sdr': {
                        'sort_options': [
                            {'value': 'activity_desc', 'label': 'Activité (haut → bas)'},
                            {'value': 'freq_asc', 'label': 'Fréquence (bas → haut)'},
                            {'value': 'freq_desc', 'label': 'Fréquence (haut → bas)'}
                        ]
                    }
                }
            })
        
        except Exception as e:
            logger.error(f"Erreur options filtres: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


    # Flask/weak_indicators/routes.py - AJOUTER CES ROUTES

    # Dans create_weak_indicators_blueprint, ajouter :

    @weak_bp.route('/api/alerts/active')
    def get_active_alerts():
        """API pour les alertes actives"""
        try:
            alerts = service.get_active_alerts()
            return jsonify({
                'success': True,
                'alerts': [alert.to_dict() if hasattr(alert, 'to_dict') else alert for alert in alerts],
                'count': len(alerts)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @weak_bp.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
    def acknowledge_alert(alert_id):
        """Marque une alerte comme lue"""
        try:
            success = service.acknowledge_alert(alert_id)
            return jsonify({
                'success': success,
                'message': 'Alerte marquée comme lue' if success else 'Alerte non trouvée'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @weak_bp.route('/api/alerts/acknowledge-all', methods=['POST'])
    def acknowledge_all_alerts():
        """Marque toutes les alertes comme lues"""
        try:
            # Implémenter dans service
            return jsonify({
                'success': True,
                'message': 'Toutes les alertes marquées comme lues'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @weak_bp.route('/api/alerts/stats')
    def get_alert_stats():
        """Statistiques des alertes"""
        try:
            stats = service.get_alert_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @weak_bp.route('/api/alerts/rules')
    def get_alert_rules():
        """Récupère les règles d'alertes"""
        try:
            rules = service.get_alert_rules()
            return jsonify({
                'success': True,
                'rules': rules
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @weak_bp.route('/api/alerts/test')
    def test_alert_trigger():
        """Teste le déclenchement d'alertes"""
        try:
            # Créer des données de test
            test_financial = {
                'symbol': '^TEST',
                'name': 'Test Index',
                'current_price': 1000,
                'change_percent': -8.5,  # Va déclencher crash
                'volume': 1000000,
                'timestamp': datetime.utcnow(),
                'source': 'test',
                'category': 'index'
            }
            
            test_travel = {
                'country_code': 'TEST',
                'country_name': 'Test Country',
                'risk_level': 4,  # Va déclencher do_not_travel
                'source': 'test',
                'summary': 'Test alert',
                'last_updated': datetime.utcnow()
            }
            
            # Vérifier les alertes
            fin_alerts = service.alert_manager.check_financial_data([test_financial])
            travel_alerts = service.alert_manager.check_travel_data([test_travel])
            
            return jsonify({
                'success': True,
                'financial_alerts': [a.to_dict() for a in fin_alerts],
                'travel_alerts': [a.to_dict() for a in travel_alerts],
                'message': 'Test terminé'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # IMPORTANT: Retourner le blueprint, pas jsonify
    return weak_bp
