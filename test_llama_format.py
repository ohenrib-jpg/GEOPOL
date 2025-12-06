import requests

# Test 1: Format simple (ce que j'ai mis dans le code)
print("=" * 70)
print("TEST 1: Format SIMPLE")
print("=" * 70)

response1 = requests.post(
    "http://localhost:8080/completion",
    json={
        "prompt": """Tu es un analyste. Voici un article:

Article: "Tensions en Ukraine: situation critique"

Analyse cet article en 50 mots.""",
        "max_tokens": 150,
        "temperature": 0.7
    },
    timeout=60
)

print(f"Code: {response1.status_code}")
result1 = response1.json()
print(f"Réponse:\n{result1.get('content', 'ERREUR')}\n")

# Test 2: Format ChatML (ancien)
print("=" * 70)
print("TEST 2: Format CHATML")
print("=" * 70)

response2 = requests.post(
    "http://localhost:8080/completion",
    json={
        "prompt": """<|im_start|>system
Tu es un analyste.<|im_end|>
<|im_start|>user
Article: "Tensions en Ukraine"
Analyse en 50 mots.<|im_end|>
<|im_start|>assistant
""",
        "max_tokens": 150,
        "temperature": 0.7,
        "stop": ["<|im_end|>"]
    },
    timeout=60
)

print(f"Code: {response2.status_code}")
result2 = response2.json()
print(f"Réponse:\n{result2.get('content', 'ERREUR')}\n")

# Test 3: Format instruction (Llama 3 natif)
print("=" * 70)
print("TEST 3: Format INSTRUCTION")
print("=" * 70)

response3 = requests.post(
    "http://localhost:8080/completion",
    json={
        "prompt": """### Instruction:
Tu es un analyste géopolitique. Analyse l'article suivant en 50 mots.

### Article:
"Tensions en Ukraine: situation critique"

### Analyse:
""",
        "max_tokens": 150,
        "temperature": 0.7
    },
    timeout=60
)

print(f"Code: {response3.status_code}")
result3 = response3.json()
print(f"Réponse:\n{result3.get('content', 'ERREUR')}\n")

print("=" * 70)
print("QUEL TEST FONCTIONNE LE MIEUX ?")
print("=" * 70)