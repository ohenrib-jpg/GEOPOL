# install_sdr_module.py
"""
Script d'installation du module SDR géopolitique
"""

import os
import sys
from pathlib import Path

def install_sdr_module():
    """Installe le module SDR dans GEOPOL"""
    
    base_dir = Path(__file__).parent
    geopol_data_dir = base_dir / "Flask" / "geopol_data"
    
    print("📡 Installation du module SDR Géopolitique...")
    
    # 1. Copier les fichiers
    files_to_copy = {
        'sdr_analyzer.py': geopol_data_dir / 'sdr_analyzer.py',
        'sdr_routes.py': geopol_data_dir / 'sdr_routes.py',
        'sdr_overlay.py': geopol_data_dir / 'overlays' / 'sdr_overlay.py',
    }
    
    for file_name, dest_path in files_to_copy.items():
        # Vérifier si le dossier existe
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copier le fichier
        source = base_dir / file_name
        if source.exists():
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ {file_name} → {dest_path}")
    
    # 2. Mettre à jour __init__.py
    init_file = geopol_data_dir / '__init__.py'
    if init_file.exists():
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajouter l'import SDR
        if 'SDRAnalyzer' not in content:
            content = content.replace(
                'from .models import CountrySnapshot, GeopoliticalIndex',
                'from .models import CountrySnapshot, GeopoliticalIndex\nfrom .sdr_analyzer import SDRAnalyzer'
            )
        
        # Ajouter à __all__
        if '__all__' in content:
            content = content.replace(
                "'GeopoliticalIndex',",
                "'GeopoliticalIndex',\n    'SDRAnalyzer',"
            )
        
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ __init__.py mis à jour")
    
    # 3. Créer le dossier static
    static_dir = base_dir.parent / "static"
    js_dir = static_dir / "js"
    css_dir = static_dir / "css"
    
    js_dir.mkdir(parents=True, exist_ok=True)
    css_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Créer les fichiers static
    js_content = '''
// static/js/sdr_layer.js
// (Le contenu du fichier JavaScript ci-dessus)
'''
    
    css_content = '''
/* static/css/sdr_layer.css */
/* (Le contenu du fichier CSS ci-dessus) */
'''
    
    with open(js_dir / "sdr_layer.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    
    with open(css_dir / "sdr_layer.css", "w", encoding="utf-8") as f:
        f.write(css_content)
    
    print("  ✅ Fichiers static créés")
    
    # 5. Mettre à jour le template principal
    templates_dir = base_dir.parent / "templates"
    if (templates_dir / "base.html").exists():
        base_html = templates_dir / "base.html"
        with open(base_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Ajouter le CSS
        if 'sdr_layer.css' not in html_content:
            html_content = html_content.replace(
                '</head>',
                '    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/sdr_layer.css\') }}">\n    </head>'
            )
        
        # Ajouter le JS
        if 'sdr_layer.js' not in html_content:
            html_content = html_content.replace(
                '</body>',
                '    <script src="{{ url_for(\'static\', filename=\'js/sdr_layer.js\') }}"></script>\n    </body>'
            )
        
        with open(base_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("  ✅ Template base.html mis à jour")
    
    print("\n🎯 Installation terminée !")
    print("\nProchaines étapes:")
    print("1. Redémarrer l'application Flask")
    print("2. Accéder à /api/sdr/health pour tester")
    print("3. Ajouter la couche SDR à votre interface Leaflet")
    print("\n📡 Mode SDR: Activez GEOPOL_REAL_MODE=true pour les données réelles")

if __name__ == '__main__':
    install_sdr_module()