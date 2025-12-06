import sys
import os

print("=== DIAGNOSTIC COMPLET ===")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")
print(f"Flask directory: {os.path.dirname(__file__)}")

print("\n=== PACKAGES INSTALLÉS ===")
try:
    import pkg_resources
    packages = [pkg.key for pkg in pkg_resources.working_set]
    print(f"xhtml2pdf installed: {'xhtml2pdf' in packages}")
    if 'xhtml2pdf' in packages:
        xhtml2pdf_info = pkg_resources.get_distribution('xhtml2pdf')
        print(f"xhtml2pdf version: {xhtml2pdf_info.version}")
        print(f"xhtml2pdf location: {xhtml2pdf_info.location}")
except Exception as e:
    print(f"Erreur pkg_resources: {e}")

print("\n=== TEST IMPORT xhtml2pdf ===")
try:
    from xhtml2pdf import pisa
    print("✅ SUCCÈS: xhtml2pdf importé avec succès")
    print(f"pisa module: {pisa}")
except ImportError as e:
    print(f"❌ ÉCHEC: {e}")
    print("Tentative d'import direct...")
    try:
        import xhtml2pdf
        print(f"✅ xhtml2pdf importé: {xhtml2pdf}")
        print(f"Dir: {[x for x in dir(xhtml2pdf) if not x.startswith('_')]}")
    except ImportError as e2:
        print(f"❌ Échec complet: {e2}")

print("\n=== VARIABLES D'ENVIRONNEMENT ===")
print(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Non défini')}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Non défini')}")