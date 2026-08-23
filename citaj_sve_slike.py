import fitz
from pathlib import Path

osnovni_folder = Path(r"D:\Dokumenti")
izlazni_folder = Path(r"D:\Birogemini\ekstrahovane_slike")
izlazni_folder.mkdir(parents=True, exist_ok=True)

def masovno_izvuci_slike():
    ukupno_slika = 0
    
    # rglob traži sve fajlove u svim subfolderima
    for pdf_putanja in osnovni_folder.rglob("*"):
        # Proveravamo da li je PDF (bez obzira da li piše .pdf ili .Pdf)
        if pdf_putanja.is_file() and pdf_putanja.suffix.lower() == '.pdf':
            print(f"Obrađujem: {pdf_putanja.name}")
            
            try:
                pdf = fitz.open(pdf_putanja)
                for broj_strane in range(len(pdf)):
                    slike = pdf[broj_strane].get_images(full=True)
                    for index_slike, slika in enumerate(slike):
                        baza_slike = pdf.extract_image(slika[0])
                        
                        # Generišemo sigurno ime fajla (sklanjamo razmake)
                        cisto_ime = pdf_putanja.stem.replace(" ", "_").replace(".", "")
                        ime_slike = f"{cisto_ime}_str{broj_strane + 1}_sl{index_slike + 1}.{baza_slike['ext']}"
                        
                        with open(izlazni_folder / ime_slike, "wb") as f:
                            f.write(baza_slike["image"])
                        ukupno_slika += 1
            except Exception as e:
                print(f"Greška na {pdf_putanja.name}: {e}")
                
    print(f"\n✅ Operacija završena! Ukupno izvučeno {ukupno_slika} slika iz svih PDF-ova.")

if __name__ == "__main__":
    masovno_izvuci_slike()