import os
from pathlib import Path

# Putanja do tvojih dokumenata
dokumenti_dir = Path(r"D:\Dokumenti")

def skeniraj_direktorijum(putanja):
    print(f"--- Započinjem analizu foldera: {putanja} ---")
    
    # Proveravamo da li folder uopšte postoji
    if not putanja.exists():
        print("Greška: Folder nije pronađen. Proveri putanju.")
        return

    brojac_pdf = 0
    brojac_docx = 0
    brojac_slika = 0

    # rglob('*') prolazi kroz sve fajlove i subfoldere
    for fajl in putanja.rglob('*'):
        if fajl.is_file():
            ekstenzija = fajl.suffix.lower()
            print(f"Pronađen fajl: {fajl.name} (u folderu: {fajl.parent.name})")
            
            if ekstenzija == '.pdf':
                brojac_pdf += 1
            elif ekstenzija == '.docx':
                brojac_docx += 1
            elif ekstenzija in ['.jpg', '.jpeg', '.png']:
                brojac_slika += 1

    print("\n--- REZULTAT ANALIZE ---")
    print(f"Ukupno PDF dokumenata: {brojac_pdf}")
    print(f"Ukupno DOCX dokumenata: {brojac_docx}")
    print(f"Ukupno slika: {brojac_slika}")

# Pokretanje funkcije
if __name__ == "__main__":
    skeniraj_direktorijum(dokumenti_dir)