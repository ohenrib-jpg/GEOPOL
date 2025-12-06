#!/usr/bin/env python3
"""
Script de test pour la fonctionnalité IA Llama
Teste la connexion et génère un rapport d'exemple
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Flask.llama_client import get_llama_client
from datetime import datetime

def test_connection():
    """Teste la connexion au serveur Llama"""
    print("=" * 60)
    print("TEST 1: Connexion au serveur Llama")
    print("=" * 60)
    
    client = get_llama_client()
    
    if client.test_connection():
        print("✅ Serveur Llama accessible sur http://localhost:8080")
        return True
    else:
        print("❌ Serveur Llama inaccessible")
        print("💡 Vérifiez que llama.cpp est lancé avec:")
        print("   cd llama.cpp && ./llama-server -m models/llama-3.2-3B-Instruct-Q4_K_M.gguf")
        return False

def test_generation():
    """Teste la génération d'un rapport"""
    print("\n" + "=" * 60)
    print("TEST 2: Génération d'un rapport géopolitique")
    print("=" * 60)
    
    client = get_llama_client()
    
    # Articles d'exemple
    sample_articles = [
        {
            'title': 'Tensions diplomatiques en Asie-Pacifique',
            'content': 'Les relations entre grandes puissances se dégradent...',
            'pub_date': '2024-01-15',
            'sentiment': 'negative',
            'source': 'Reuters'
        },
        {
            'title': 'Sommet européen sur la sécurité énergétique',
            'content': 'Les dirigeants européens discutent de diversification...',
            'pub_date': '2024-01-16',
            'sentiment': 'neutral',
            'source': 'AFP'
        },
        {
            'title': 'Accord commercial prometteur en Afrique',
            'content': 'Nouvelle zone de libre-échange signée...',
            'pub_date': '2024-01-17',
            'sentiment': 'positive',
            'source': 'BBC'
        }
    ]
    
    context = {
        'period': '15/01/2024 → 17/01/2024',
        'themes': ['Géopolitique', 'Économie'],
        'sentiment_positive': 1,
        'sentiment_negative': 1,
        'sentiment_neutral': 1,
        'total_articles': 3
    }
    
    print(f"📊 Test avec {len(sample_articles)} articles")
    print(f"📅 Période: {context['period']}")
    print(f"🎯 Thèmes: {', '.join(context['themes'])}")
    print("\n⏳ Génération en cours...")
    
    result = client.generate_analysis(
        report_type='geopolitique',
        articles=sample_articles,
        context=context
    )
    
    if result['success']:
        print("✅ Génération réussie!")
        print(f"📝 Longueur: {len(result['analysis'])} caractères")
        print(f"🤖 Modèle: {result.get('model_used', 'N/A')}")
        print(f"🔢 Tokens générés: {result.get('completion_tokens', 'N/A')}")
        print("\n" + "─" * 60)
        print("EXTRAIT DU RAPPORT:")
        print("─" * 60)
        print(result['analysis'][:500] + "...")
        print("─" * 60)
        return True
    else:
        print(f"❌ Échec de la génération")
        print(f"Erreur: {result.get('error')}")
        print("\n📋 MODE DÉGRADÉ:")
        print(result['analysis'][:500] + "...")
        return False

def test_different_types():
    """Teste différents types de rapports"""
    print("\n" + "=" * 60)
    print("TEST 3: Génération multi-types")
    print("=" * 60)
    
    client = get_llama_client()
    
    report_types = ['geopolitique', 'economique', 'securite', 'synthese']
    
    sample_articles = [{
        'title': 'Événement test',
        'content': 'Contenu test',
        'pub_date': datetime.now().strftime('%Y-%m-%d'),
        'sentiment': 'neutral',
        'source': 'Test'
    }]
    
    context = {
        'period': 'Test',
        'themes': ['Test'],
        'sentiment_positive': 0,
        'sentiment_negative': 0,
        'sentiment_neutral': 1,
        'total_articles': 1
    }
    
    results = {}
    
    for report_type in report_types:
        print(f"\n📊 Test rapport: {report_type}")
        result = client.generate_analysis(
            report_type=report_type,
            articles=sample_articles,
            context=context
        )
        
        if result['success']:
            print(f"  ✅ {report_type}: OK ({len(result['analysis'])} chars)")
            results[report_type] = 'OK'
        else:
            print(f"  ❌ {report_type}: ÉCHEC - {result.get('error')}")
            results[report_type] = 'ÉCHEC'
    
    print("\n" + "─" * 60)
    print("RÉSUMÉ:")
    print("─" * 60)
    for report_type, status in results.items():
        emoji = "✅" if status == "OK" else "❌"
        print(f"{emoji} {report_type}: {status}")
    
    return all(status == 'OK' for status in results.values())

def main():
    """Fonction principale"""
    print("\n" + "=" * 60)
    print("🧪 TEST DE LA FONCTIONNALITÉ IA LLAMA")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Endpoint: http://localhost:8080")
    print("=" * 60)
    
    tests_results = []
    
    # Test 1: Connexion
    tests_results.append(('Connexion', test_connection()))
    
    if not tests_results[0][1]:
        print("\n⚠️ Tests interrompus: serveur Llama non disponible")
        print("\n📖 Pour lancer le serveur Llama:")
        print("   cd llama.cpp")
        print("   ./llama-server -m models/llama-3.2-3B-Instruct-Q4_K_M.gguf -c 2048")
        return 1
    
    # Test 2: Génération
    tests_results.append(('Génération', test_generation()))
    
    # Test 3: Multi-types
    tests_results.append(('Multi-types', test_different_types()))
    
    # Rapport final
    print("\n" + "=" * 60)
    print("📊 RAPPORT FINAL")
    print("=" * 60)
    
    for test_name, success in tests_results:
        emoji = "✅" if success else "❌"
        print(f"{emoji} {test_name}: {'RÉUSSI' if success else 'ÉCHOUÉ'}")
    
    total_success = sum(1 for _, success in tests_results if success)
    total_tests = len(tests_results)
    
    print("=" * 60)
    print(f"Score: {total_success}/{total_tests} tests réussis")
    print("=" * 60)
    
    if total_success == total_tests:
        print("\n🎉 Tous les tests sont passés!")
        return 0
    else:
        print(f"\n⚠️ {total_tests - total_success} test(s) échoué(s)")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
