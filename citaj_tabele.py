import pdfplumber
from pathlib import Path

pdf_fajl = Path(r"D:\Dokumenti\osnove\1605_Donji PEK_2025-2026.pdf")

def probno_citanje_tabela(putanja):
    print(f"⏳ Skeniram PDF u potrazi za tabelama: {putanja.name}...\n")
    
    try:
        # Otvaramo PDF pomoću pdfplumber-a
        with pdfplumber.open(putanja) as pdf:
            # Proći ćemo kroz prvih 15 stranica da nađemo neku tabelu
            for broj_strane, stranica in enumerate(pdf.pages[:15]): 
                # extract_tables() automatski detektuje linije tabela
                tabele = stranica.extract_tables()
                
                if tabele:
                    print(f"✅ Pronađeno {len(tabele)} tabela na stranici {broj_strane + 1}:")
                    
                    for index_tabele, tabela in enumerate(tabele):
                        print(f"\n--- Tabela {index_tabele + 1} ---")
                        
                        # Tabela je zapravo lista (redovi) koja sadrži liste (kolone)
                        # Štampamo prva 4 reda svake tabele da vidimo strukturu
                        for red in tabela[:4]:
                            # Čistimo 'None' vrednosti ako je polje u tabeli prazno
                            ociscen_red = [celija if celija is not None else "" for celija in red]
                            print(ociscen_red)
                        
                        if len(tabela) > 4:
                            print("... (ima još redova)")
                    print("-" * 40)
                    
    except Exception as e:
        print(f"❌ Greška prilikom čitanja: {e}")

if __name__ == "__main__":
    if pdf_fajl.exists():
        probno_citanje_tabela(pdf_fajl)
    else:
        print("Fajl nije pronađen.")