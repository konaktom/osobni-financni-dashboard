import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry

# Importujeme naše vlastní třídy ze souboru logika.py
from logika import SpravceRozpoctu, Prijem, Vydaj


class FinancniDashboard:
    """Třída zajišťující grafické uživatelské rozhraní (GUI) a vykreslování grafů."""

    def __init__(self, root: tk.Tk, spravce: SpravceRozpoctu):
        self.root = root
        self.spravce = spravce  # Kompozice: GUI v sobě drží odkaz na správce rozpočtu
        self.root.title("Osobní finanční dashboard")
        self.root.geometry("1050x620")

        # Rozdělení hlavního okna na levý panel (ovládání a historie) a pravý panel (grafy)
        self.frame_levy = tk.Frame(root, padx=20, pady=15)
        self.frame_levy.pack(side=tk.LEFT, fill=tk.Y)

        self.frame_pravy = tk.Frame(root, padx=20, pady=15)
        self.frame_pravy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Vykreslení jednotlivých částí obrazovky
        self.vykresli_formular()
        self.vykresli_historii_a_filtr()
        self.vykresli_ovladani_grafu()

        # Prvotní naplnění daty při spuštění programu
        self.aktualizuj_dashboard()

    def vykresli_formular(self) -> None:
        """Vytvoří formulář pro zadávání nových příjmů a výdajů."""
        self.lbl_zustatek = tk.Label(
            self.frame_levy, text="Celkový zůstatek: 0.00 Kč", font=("Arial", 14, "bold")
        )
        self.lbl_zustatek.pack(pady=(0, 10), anchor="w")

        # 1. Výběr data pomocí kalendáře (tkcalendar)
        tk.Label(self.frame_levy, text="Datum transakce:").pack(anchor="w")
        self.entry_datum = DateEntry(
            self.frame_levy,
            width=18,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd"
        )
        self.entry_datum.pack(fill=tk.X, pady=(0, 5))

        # 2. Částka
        tk.Label(self.frame_levy, text="Částka (Kč):").pack(anchor="w")
        self.entry_castka = tk.Entry(self.frame_levy)
        self.entry_castka.pack(fill=tk.X, pady=(0, 5))

        # 3. Rozbalovací seznam kategorií (lze vybrat i vepsat vlastní)
        tk.Label(self.frame_levy, text="Kategorie:").pack(anchor="w")
        kategorie_moznosti = [
            "Jídlo", "Bydlení", "Doprava", "Zábava", "Oblečení", "Výplata", "Brigáda", "Ostatní"
        ]
        self.entry_kategorie = ttk.Combobox(self.frame_levy, values=kategorie_moznosti)
        self.entry_kategorie.set("Ostatní")
        self.entry_kategorie.pack(fill=tk.X, pady=(0, 5))

        # 4. Popis transakce
        tk.Label(self.frame_levy, text="Popis:").pack(anchor="w")
        self.entry_popis = tk.Entry(self.frame_levy)
        self.entry_popis.pack(fill=tk.X, pady=(0, 5))

        # 5. Přepínač typu transakce (Výdaj / Příjem)
        frame_typ = tk.Frame(self.frame_levy)
        frame_typ.pack(fill=tk.X, pady=5)
        self.var_typ = tk.StringVar(value="Vydaj")
        tk.Radiobutton(frame_typ, text="Výdaj (-)", variable=self.var_typ, value="Vydaj").pack(side=tk.LEFT)
        tk.Radiobutton(frame_typ, text="Příjem (+)", variable=self.var_typ, value="Prijem").pack(side=tk.LEFT, padx=15)

        # 6. Tlačítko pro uložení
        tk.Button(
            self.frame_levy,
            text="Přidat transakci",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.zpracuj_formular
        ).pack(fill=tk.X, pady=(5, 15))

    def vykresli_historii_a_filtr(self) -> None:
        """Vytvoří filtrování podle měsíců a seznam transakcí."""
        frame_filtr = tk.Frame(self.frame_levy)
        frame_filtr.pack(fill=tk.X, pady=(0, 5))

        tk.Label(frame_filtr, text="Filtrovat měsíc:").pack(side=tk.LEFT)
        self.combo_filtr_mesic = ttk.Combobox(frame_filtr, values=["Vše"], state="readonly", width=12)
        self.combo_filtr_mesic.set("Vše")
        self.combo_filtr_mesic.pack(side=tk.RIGHT)

        # Při změně měsíce v rozbalovacím seznamu se dashboard automaticky přepočítá
        self.combo_filtr_mesic.bind("<<ComboboxSelected>>", lambda event: self.aktualizuj_dashboard())

        tk.Label(self.frame_levy, text="Historie transakcí:").pack(anchor="w")

        # Rámeček pro seznam a posuvník (Scrollbar)
        frame_seznam = tk.Frame(self.frame_levy)
        frame_seznam.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame_seznam)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.seznam = tk.Listbox(frame_seznam, width=50, height=12, yscrollcommand=scrollbar.set)
        self.seznam.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.seznam.yview)

    def vykresli_ovladani_grafu(self) -> None:
        """Vytvoří horní lištu v pravém panelu pro přepínání typu grafu."""
        frame_prepinac = tk.Frame(self.frame_pravy)
        frame_prepinac.pack(fill=tk.X, pady=(0, 10))

        tk.Label(frame_prepinac, text="Zobrazit graf:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.var_graf = tk.StringVar(value="kategorie")
        tk.Radiobutton(
            frame_prepinac,
            text="Výdaje dle kategorií (koláčový)",
            variable=self.var_graf,
            value="kategorie",
            command=self.aktualizuj_dashboard
        ).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(
            frame_prepinac,
            text="Porovnání měsíců (sloupcový)",
            variable=self.var_graf,
            value="mesice",
            command=self.aktualizuj_dashboard
        ).pack(side=tk.LEFT)

        # Kontejner, do kterého se bude vkládat samotný graf z knihovny matplotlib
        self.frame_graf = tk.Frame(self.frame_pravy)
        self.frame_graf.pack(fill=tk.BOTH, expand=True)

    def zpracuj_formular(self) -> None:
        """Načte hodnoty z formuláře, vytvoří příslušný objekt a uloží ho přes správce."""
        try:
            # Převedeme případnou desetinnou čárku na tečku, aby float() nespadl
            text_castky = self.entry_castka.get().replace(",", ".")
            castka = float(text_castky)
            kategorie = self.entry_kategorie.get()
            popis = self.entry_popis.get()
            datum = self.entry_datum.get()

            # Vytvoření konkrétní instance potomka (Polymorfismus)
            if self.var_typ.get() == "Prijem":
                nova_transakce = Prijem(castka, kategorie, popis, datum)
            else:
                nova_transakce = Vydaj(castka, kategorie, popis, datum)

            # Předání objektu správci rozpočtu
            self.spravce.pridej_transakci(nova_transakce)

            # Vyčištění políček po úspěšném uložení
            self.entry_castka.delete(0, tk.END)
            self.entry_popis.delete(0, tk.END)

            self.aktualizuj_dashboard()

        except ValueError as chyba:
            # Zachycení chyby (např. text místo čísla nebo záporná částka z třídy Transakce)
            messagebox.showerror("Neplatný vstup", f"Zkontrolujte zadané údaje:\n{chyba}")

    def aktualizuj_dashboard(self) -> None:
        """Obnoví zůstatek, nabídku měsíců, seznam historie i aktuální graf."""
        # 1. Aktualizace celkového zůstatku a jeho barvy
        zustatek = self.spravce.celkovy_zustatek()
        barva = "darkgreen" if zustatek >= 0 else "red"
        self.lbl_zustatek.config(text=f"Celkový zůstatek: {zustatek:.2f} Kč", fg=barva)

        # 2. Aktualizace nabídky dostupných měsíců ve filtru
        aktualni_vyber = self.combo_filtr_mesic.get()
        dostupne_mesice = ["Vše"] + self.spravce.ziskej_dostupne_mesice()
        self.combo_filtr_mesic["values"] = dostupne_mesice
        if aktualni_vyber not in dostupne_mesice:
            self.combo_filtr_mesic.set("Vše")
            aktualni_vyber = "Vše"

        # 3. Naplnění seznamu historie (od nejnovějších záznamů)
        self.seznam.delete(0, tk.END)
        filtrovane = self.spravce.filtruj_podle_mesice(aktualni_vyber)
        for t in reversed(filtrovane):
            znamenko = "+" if isinstance(t, Prijem) else "-"
            # Čteme veřejnou property t.castka (respektujeme zapouzdření)
            radek = f"{t.datum} | {znamenko}{t.castka:.2f} Kč ({t.kategorie}) - {t.popis}"
            self.seznam.insert(tk.END, radek)

        # 4. Překreslení grafu
        self.vykresli_graf(aktualni_vyber)

    def vykresli_graf(self, vybrany_mesic: str) -> None:
        """Vykreslí koláčový nebo sloupcový graf podle zvoleného režimu."""
        # Odstraníme starý graf a uvolníme paměť matplotlibu
        for widget in self.frame_graf.winfo_children():
            widget.destroy()
        plt.close("all")

        fig, ax = plt.subplots(figsize=(6, 4.5))

        if self.var_graf.get() == "kategorie":
            # Koláčový graf výdajů pro vybraný měsíc
            data_kategorie = self.spravce.vydaje_podle_kategorii(vybrany_mesic)
            if data_kategorie:
                ax.pie(
                    data_kategorie.values(),
                    labels=data_kategorie.keys(),
                    autopct="%1.1f%%",
                    startangle=90
                )
                ax.set_title(f"Rozložení výdajů podle kategorií ({vybrany_mesic})")
            else:
                ax.text(0.5, 0.5, "Žádné výdaje pro vybrané období", ha="center", va="center")
                ax.axis("off")

        else:
            # Sloupcový graf porovnávající celkové příjmy a výdaje po měsících
            prehled = self.spravce.mesicni_prehled()
            if prehled:
                mesice = list(prehled.keys())
                prijmy = [prehled[m]["prijmy"] for m in mesice]
                vydaje = [prehled[m]["vydaje"] for m in mesice]

                pozice = range(len(mesice))
                sirka = 0.35

                # Dva sloupce vedle sebe pro každý měsíc (posunuté o polovinu šířky)
                ax.bar([i - sirka / 2 for i in pozice], prijmy, width=sirka, label="Příjmy", color="#4CAF50")
                ax.bar([i + sirka / 2 for i in pozice], vydaje, width=sirka, label="Výdaje", color="#F44336")

                ax.set_xticks(list(pozice))
                ax.set_xticklabels(mesice, rotation=30)
                ax.set_ylabel("Částka (Kč)")
                ax.set_title("Měsíční porovnání příjmů a výdajů")
                ax.legend()
                fig.tight_layout()
            else:
                ax.text(0.5, 0.5, "Zatím nejsou zadány žádné transakce", ha="center", va="center")
                ax.axis("off")

        # Vložení grafu matplotlib přímo do okna tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.frame_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)