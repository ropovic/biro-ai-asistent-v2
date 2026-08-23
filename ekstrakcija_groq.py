import os
import json
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from pdfminer.high_level import extract_text

# Učitavamo promenljive iz .env fajla (tu se nalazi naš ključ)
load_dotenv()

# Inicijalizujemo Groq klijent - on automatski nalazi GROQ_API_KEY
client = Groq()

# Testiramo na prvom dokumentu
pdf_fajl = Path(r"D:\Dokumenti\osnove\1605_Donji PEK_2025-2026.pdf")

def izvuci_metapodatke(putanja):
    print(f"⏳ Čitam početak dokumenta {putanja.name}...")
    
    # Čitamo ceo tekst, ali ćemo za analizu odseći samo prvih 4000 karaktera
    ceo_tekst = extract_text(putanja)
    tekst_za_analizu = ceo_tekst[:4000] 
    
    # Pišemo prompt za Llama 3.1 model
    prompt = f"""
    Ti si stručni asistent za ekstrakciju podataka iz šumarskih dokumenata (Osnove gazdovanja šumama).
    Pročitaj sledeći tekst i izvuci tražene podatke. 
    Vrati rezultat ISKLJUČIVO kao JSON objekat, bez ikakvog dodatnog teksta, markdauna ili objašnjenja.
    Moraš koristiti tačno ove ključeve:
    - "gazdinska_jedinica": (ime gazdinske jedinice)
    - "sumsko_gazdinstvo": (ime šumskog gazdinstva)
    - "sumska_uprava": (ime šumske uprave)
    - "opstina_okrug": (ime opštine ili okruga kojem pripada)
    - "povrsina_ha": (površina u hektarima samo broj ako se pominje, inače null)
    - "koordinate": (geografske koordinate ako se pominju, inače null)
    
    Tekst za analizu:
    {tekst_za_analizu}
    """
    
    print("🤖 Šaljem tekst Groq LLM-u na analizu (Llama-3.1-70B)...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            # 70B Versatile je sjajan, brz model koji odlično priča srpski
            model="qwen/qwen3.6-27b", 
            # Teramo model da vrati validan JSON
            response_format={"type": "json_object"}, 
            # Temperatura 0.1 znači da želimo tačne podatke, a ne kreativnost
            temperature=0.1 
        )
        
        rezultat = chat_completion.choices[0].message.content
        
        # Parsiramo JSON da proverimo da li je struktura ispravna
        json_podaci = json.loads(rezultat)
        
        print("\n✅ Ekstrakcija uspešna! Ovo je dobijeni JSON rezultat:")
        print(json.dumps(json_podaci, indent=4, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Greška prilikom komunikacije sa Groq API-jem: {e}")

if __name__ == "__main__":
    if pdf_fajl.exists():
        izvuci_metapodatke(pdf_fajl)
    else:
        print("Fajl nije pronađen.")