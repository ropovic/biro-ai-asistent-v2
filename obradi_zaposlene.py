import os
import json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

folder_zaposleni = Path(r"D:\Dokumenti\zaposleni")
excel_putanja = Path(r"D:\Birogemini\venv\Fotobaza.xlsx")

def skeniraj_zaposlene():
    print(f"⏳ Čitam Excel bazu sa R2 linkovima i funkcijama: {excel_putanja.name}...")
    
    r2_mape = {}
    funkcije_mape = {}
    
    if excel_putanja.exists():
        df = pd.read_excel(excel_putanja)
        print(f"📊 Pronađene kolone u Excelu: {list(df.columns)}")
        
        for _, row in df.iterrows():
            objekat = str(row.get('Objekat', '')).strip()
            link = str(row.get('Link', '')).strip()
            funkcija = str(row.get('Funkcija', '')).strip()
            
            if objekat and objekat != 'nan':
                r2_mape[objekat] = link
                funkcije_mape[objekat] = funkcija
    else:
        print("⚠️ Upozorenje: Fotobaza.xlsx nije pronađena.")

    baza_zaposlenih = []
    print(f"\n⏳ Skeniram zaposlene u folderu {folder_zaposleni}...")
    
    for txt_fajl in folder_zaposleni.glob("*.txt"):
        ime_fajla = txt_fajl.stem
        
        # Preskačemo logotipe jer služe za UI
        if "logo" in ime_fajla.lower():
            print(f"🎨 Preskočen logotip (za UI): {ime_fajla}")
            continue

        try:
            # Čitamo tekst u promenljivu bez ikakvih dijakritika
            with open(txt_fajl, "r", encoding="utf-8") as f:
                opis_tekst = f.read().strip()
            
            osnova_imena = ime_fajla.replace("Foto_", "").replace("_", " ")
            
            kljuc_jpg = f"{osnova_imena}.jpg"
            r2_url = r2_mape.get(kljuc_jpg, r2_mape.get(osnova_imena, ""))
            funkcija_zaposlenog = funkcije_mape.get(kljuc_jpg, funkcije_mape.get(osnova_imena, "zaposleni"))
            
            zaposleni_info = {
                "ime_prezime": osnova_imena,
                "funkcija": funkcija_zaposlenog if funkcija_zaposlenog != 'nan' else "zaposleni",
                "opis": opis_tekst,
                "r2_url": r2_url
            }
            
            baza_zaposlenih.append(zaposleni_info)
            print(f"✅ Obrađen: {osnova_imena} -> [{zaposleni_info['funkcija']}]")
            
        except Exception as e:
            print(f"❌ Greška kod fajla {txt_fajl.name}: {e}")

    izlazni_json = Path(r"D:\Birogemini\zaposleni_baza.json")
    with open(izlazni_json, "w", encoding="utf-8") as out:
        json.dump(baza_zaposlenih, out, indent=4, ensure_ascii=False)
        
    print(f"\n🎉 Uspešno obrađeno i mapirano {len(baza_zaposlenih)} zaposlenih!")
    print(f"📁 Sačuvana baza: {izlazni_json}")

if __name__ == "__main__":
    skeniraj_zaposlene()