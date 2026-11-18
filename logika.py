import json
import os
from datetime import datetime


# ==========================================
# 1. DATOVÉ MODELY (Dědičnost, Polymorfismus, Zapouzdření)
# ==========================================

class Transakce:
    """Základní (rodičovská) třída reprezentující obecný finanční pohyb."""

    def __init__(self, castka: float, kategorie: str, popis: str, datum: str = None):
        # Kontrola vstupních dat (ochrana proti nesmyslným hodnotám)
        if castka <= 0:
            raise ValueError("Částka musí být kladné číslo větší než nula.")
        if not kategorie or not kategorie.strip():
            raise ValueError("Kategorie nesmí být prázdná.")

        # Zapouzdření: atribut _castka je chráněný před přímým přepsáním zvenčí
        self._castka = float(castka)
        self.kategorie = kategorie.strip()
        self.popis = popis.strip()

        # Pokud datum není zadáno, použije se dnešní; jinak ověříme správný formát
        if datum:
            datetime.strptime(datum, "%Y-%m-%d")
            self.datum = datum
        else:
            self.datum = datetime.now().strftime("%Y-%m-%d")

    @property
    def castka(self) -> float:
        """Veřejný getter pro bezpečné čtení zapouzdřené částky."""
        return self._castka

    def ziskej_hodnotu(self) -> float:
        """Abstraktní metoda – potomci ji přepíší podle toho, zda jde o příjem či výdaj."""
        raise NotImplementedError("Tato metoda musí být implementována v potomcích.")

    def __str__(self) -> str:
        """Magická metoda pro přehledný textový výpis objektu (např. při ladění)."""
        return f"{self.datum} | {self.kategorie}: {self.popis} ({self._castka:.2f} Kč)"

    def do_slovniku(self) -> dict:
        """Převede objekt na slovník, aby šel uložit do souboru JSON."""
        return {
            "typ": self.__class__.__name__,
            "castka": self._castka,
            "kategorie": self.kategorie,
            "popis": self.popis,
            "datum": self.datum
        }


class Prijem(Transakce):
    """Potomek třídy Transakce – reprezentuje příchozí peníze."""

    def ziskej_hodnotu(self) -> float:
        # Polymorfismus: příjem ovlivňuje celkový zůstatek kladně
        return self._castka


class Vydaj(Transakce):
    """Potomek třídy Transakce – reprezentuje odchozí peníze."""

    def ziskej_hodnotu(self) -> float:
        # Polymorfismus: výdaj ovlivňuje celkový zůstatek záporně
        return -self._castka


# ==========================================
# 2. ŘÍDÍCÍ TŘÍDA APLIKACE (Správa stavu a výpočty)
# ==========================================

class SpravceRozpoctu:
    """Hlavní řídící objekt, který zapouzdřuje seznam transakcí a logiku výpočtů."""

    def __init__(self, soubor_data: str = "finance_data.json"):
        self._transakce = []  # Skrytý (zapouzdřený) seznam všech objektů transakcí
        self._soubor_data = soubor_data
        self.nacti_data()

    def pridej_transakci(self, transakce: Transakce) -> None:
        """Přidá novou transakci do seznamu a okamžitě uloží změny na disk."""
        if not isinstance(transakce, Transakce):
            raise TypeError("Lze přidat pouze objekt typu Transakce.")
        self._transakce.append(transakce)
        self.uloz_data()

    def celkovy_zustatek(self) -> float:
        """Vypočítá aktuální zůstatek pomocí polymorfní metody ziskej_hodnotu()."""
        return sum(t.ziskej_hodnotu() for t in self._transakce)

    def ziskej_dostupne_mesice(self) -> list:
        """Vrátí seřazený seznam unikátních měsíců ve formátu 'YYYY-MM' (pro filtr v GUI)."""
        mesice = {t.datum[:7] for t in self._transakce}
        return sorted(list(mesice), reverse=True)

    def filtruj_podle_mesice(self, mesic: str = "Vše") -> list:
        """Vrátí transakce za konkrétní měsíc ('YYYY-MM'), nebo všechny při volbě 'Vše'."""
        if mesic == "Vše" or not mesic:
            return list(self._transakce)
        return [t for t in self._transakce if t.datum.startswith(mesic)]

    def vydaje_podle_kategorii(self, mesic: str = "Vše") -> dict:
        """Sečte výdaje po kategoriích za vybraný měsíc (podklad pro koláčový graf)."""
        soucty = {}
        for t in self.filtruj_podle_mesice(mesic):
            if isinstance(t, Vydaj):
                soucty[t.kategorie] = soucty.get(t.kategorie, 0.0) + t.castka
        return soucty

    def mesicni_prehled(self) -> dict:
        """Seskupí celkové příjmy a výdaje po měsících (podklad pro sloupcový graf)."""
        prehled = {}
        for t in self._transakce:
            mesic = t.datum[:7]  # Z data '2026-11-18' vezme první znaky '2026-11'
            if mesic not in prehled:
                prehled[mesic] = {"prijmy": 0.0, "vydaje": 0.0}

            if isinstance(t, Prijem):
                prehled[mesic]["prijmy"] += t.castka
            elif isinstance(t, Vydaj):
                prehled[mesic]["vydaje"] += t.castka

        # Vrátíme slovník seřazený chronologicky od nejstaršího měsíce po nejnovější
        return dict(sorted(prehled.items()))

    def uloz_data(self) -> None:
        """Uloží všechny objekty transakcí do JSON souboru."""
        data = [t.do_slovniku() for t in self._transakce]
        with open(self._soubor_data, "w", encoding="utf-8") as soubor:
            json.dump(data, soubor, ensure_ascii=False, indent=4)

    def nacti_data(self) -> None:
        """Načte záznamy z JSON souboru a znovu z nich vytvoří instance tříd."""
        if not os.path.exists(self._soubor_data):
            return

        with open(self._soubor_data, "r", encoding="utf-8") as soubor:
            data = json.load(soubor)
            for polozka in data:
                if polozka["typ"] == "Prijem":
                    t = Prijem(polozka["castka"], polozka["kategorie"], polozka["popis"], polozka["datum"])
                else:
                    t = Vydaj(polozka["castka"], polozka["kategorie"], polozka["popis"], polozka["datum"])
                self._transakce.append(t)
