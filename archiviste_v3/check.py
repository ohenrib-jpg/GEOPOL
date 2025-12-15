"""
Vérificateur d'indentation pour la section Archiviste
À lancer : python check_indentation.py
"""

test_code = '''
if os.path.exists(archiviste_path):
    print(f"✅ Dossier Archiviste v3 trouvé: {archiviste_path}")
try:
    if archiviste_path not in sys.path:
'''

print("="*70)
print("🔍 VÉRIFICATION INDENTATION")
print("="*70)

lines = test_code.strip().split('\n')

for i, line in enumerate(lines, 1):
    # Compter les espaces au début
    spaces = len(line) - len(line.lstrip())
    indent_level = spaces // 4
    
    # Détecter les problèmes
    issue = ""
    if 'try:' in line and spaces == 0:
        issue = "❌ PROBLÈME: try sans indentation !"
    elif 'try:' in line and spaces == 4:
        issue = "❌ PROBLÈME: try devrait avoir 8 espaces (2 niveaux)"
    elif 'try:' in line and spaces == 8:
        issue = "✅ CORRECT: try bien indenté"
    
    print(f"Ligne {i}: {spaces:2d} espaces | Niveau {indent_level} | {line}")
    if issue:
        print(f"         → {issue}")

print("\n" + "="*70)
print("💡 RÈGLE D'INDENTATION PYTHON")
print("="*70)
print("""
Niveau 0 (0 espaces)  : Instructions de niveau principal
Niveau 1 (4 espaces)  : À l'intérieur d'un if/for/while/def
Niveau 2 (8 espaces)  : À l'intérieur d'un if DANS un if
Niveau 3 (12 espaces) : À l'intérieur d'un if DANS un if DANS un if

VOTRE CAS:
if 'ARCHIVISTE_V3_SERVICE' not in app.config:     # Niveau 0
    if os.path.exists(archiviste_path):            # Niveau 1 (4 espaces)
        print("...")                                # Niveau 2 (8 espaces)
        try:                                        # Niveau 2 (8 espaces) ← ICI
            # Code                                  # Niveau 3 (12 espaces)
""")
print("="*70)
