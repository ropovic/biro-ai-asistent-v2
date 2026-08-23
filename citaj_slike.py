import fitz  # Ovo je PyMuPDF
import os
from pathlib import Path

pdf_fajl = Path(r"D:\Dokumenti\osnove\1605_Donji PEK_2025-2026.pdf")
izlazni_folder = Path(r"D:\Birogemini\ekstrahovane_slike")

def izvuci_slike_iz_pdf(putanja):
    print(f"⏳ Tražim dijagrame i slike u: {putanja.name}...\n")
    
    # Pravimo folder ako ne postoji
    if not izlazni_folder.exists():
        izlazni_folder.mkdir(parents=True, exist_ok=True)
        print(f"📁 Kreiran folder za čuvanje slika: {izlazni_folder}")

    try:
        # Otvaramo PDF dokument
        pdf = fitz.open(putanja)
        broj_izvucenih_slika = 0

        # Prolazimo kroz svaku stranicu
        for broj_strane in range(len(pdf)):
            stranica = pdf[broj_strane]
            slike_na_stranici = stranica.get_images(full=True)
            
            # Ako ima slika na ovoj stranici
            if slike_na_stranici:
                print(f"Pronađeno {len(slike_na_stranici)} slika na stranici {broj_strane + 1}.")
                
                for index_slike, slika in enumerate(slike_na_stranici):
                    xref = slika[0] # xref je jedinstveni ID slike u PDF-u
                    
                    # Pokušavamo da izvučemo samu sliku
                    baza_slike = pdf.extract_image(xref)
                    bajtovi_slike = baza_slike["image"]
                    ekstenzija = baza_slike["ext"]
                    
                    # Generišemo ime: ImeDokumenta_Strana_Broj.ekstenzija
                    # Npr: 1605_Donji_PEK_Strana_12_Slika_1.jpeg
                    ime_slike = f"{putanja.stem}_Strana_{broj_strane + 1}_Slika_{index_slike + 1}.{ekstenzija}"
                    putanja_do_slike = izlazni_folder / ime_slike
                    
                    # Čuvamo sliku na disk
                    with open(putanja_do_slike, "wb") as file_out:
                        file_out.write(bajtovi_slike)
                    
                    broj_izvucenih_slika += 1
                    
        print(f"\n✅ Gotovo! Ukupno izvučeno {broj_izvucenih_slika} slika/dijagrama.")
        print(f"Proveri folder: {izlazni_folder}")

    except Exception as e:
        print(f"❌ Greška prilikom čitanja slika: {e}")

if __name__ == "__main__":
    if pdf_fajl.exists():
        izvuci_slike_iz_pdf(pdf_fajl)
    else:
        print("Fajl nije pronađen.")