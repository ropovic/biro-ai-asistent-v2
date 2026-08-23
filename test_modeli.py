import os
from groq import Groq
from dotenv import load_dotenv

# Učitavanje varijabli (proveri samo da li se tvoj ključ u .env fajlu zove GROQ_API_KEY)
load_dotenv()
client = Groq()

print("Tražim dostupne modele...")
modeli = client.models.list()

print("\nDostupni modeli na tvom nalogu su:")
for m in modeli.data:
    print(f"- {m.id}")