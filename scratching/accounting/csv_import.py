import locale
from decimal import Decimal
import chardet, csv, pathlib

locale.setlocale(locale.LC_NUMERIC, "de_DE.UTF-8")  # German/Austria format
dot = locale.localeconv()['decimal_point']

columns = ["satzart", "konto", "buchdatum", "belegdatum", "belegnr", "betrag", "waehrung", "text", "buchtyp", "buchsymbol", "buchcode", "periode", "gegenbuchkz", "verbuchkz", "extart", "extid", "verbuchstatus", "gkonto",
           "kost", "kobetrag"]

cost_locations = [
    {"id": 1, "data": {"name": "Webling", "data": {"1": 100.0}}},
    {"id": 2, "data": {"name": "Gösting", "data": {"2": 100.0}}},
    {"id": 3, "data": {"name": "Hartberg", "data": {"3": 100.0}}},
    {"id": 4, "data": {"name": "Villach", "data": {"4": 100.0}}},
    {"id": 5, "data": {"name": "Kapfenberg", "data": {"5": 100.0}}},
    {"id": 9, "data": {"name": "Overhead/Büro", "data": {"25": 100.0}}},
]

col_konto = "konto"
col_betrag = "betrag"
col_kostenstelle = "kost"
col_kostenstelle_betrag = "kobetrag"

def get_cost_unit_by_id(unit):
    if unit == '':
        return None

    unit_id = int(unit)

    for unit in cost_locations:
        if unit["id"] == unit_id:
            return unit["data"]

    return None

def get_column(name):
    return columns.index(name)

def get_float_from(value):
    return Decimal(value.replace(dot, '.')) if value else Decimal(0)

def _strip_nuls(line):
    return line.replace('\x00', '')

def csv_reader(filename):
    dict_rows = []
    print(filename)
    with open(filename, newline='', encoding='us-ascii') as f:
        reader = csv.DictReader(f, delimiter=';')
        last_konto = None
        curr_row = 0
        for row in reader:

            if curr_row == 0:
                curr_row += 1
                continue

            konto = row['konto']
            betrag = get_float_from(row['betrag'])
            kostenstelle_data = get_cost_unit_by_id(row[col_kostenstelle])
            kostenstelle = kostenstelle_data["data"] if kostenstelle_data else None
            kostenstelle_betrag = get_float_from(row[col_kostenstelle_betrag])


            if konto:
                last_konto = konto

            current_konto = last_konto

            if betrag and kostenstelle_betrag:

                if betrag == kostenstelle_betrag:
                    dict_rows.append(
                        {
                            "konto": current_konto,
                            "kostenstelle": kostenstelle,
                            "soll": betrag,
                            "haben": Decimal(0)
                        }
                    )
                else:
                    betrag = betrag - kostenstelle_betrag

                    dict_rows.append(
                        {
                            "konto": current_konto,
                            "kostenstelle": None,
                            "soll": Decimal(0),
                            "haben": betrag
                        }
                    )

                    dict_rows.append(
                        {
                            "konto": current_konto,
                            "kostenstelle": kostenstelle,
                            "soll": Decimal(0),
                            "haben": kostenstelle_betrag
                        }
                    )

            else:
                if betrag and betrag < 0 and not kostenstelle_betrag:
                    dict_rows.append(
                        {
                            "konto": current_konto,
                            "kostenstelle": kostenstelle,
                            "soll": Decimal(0),
                            "haben": betrag
                        }
                    )
                else:
                    dict_rows.append(
                        {
                            "konto": current_konto,
                            "kostenstelle": kostenstelle,
                            "soll": kostenstelle_betrag,
                            "haben": Decimal(0)
                        }
                    )

            curr_row += 1

    return dict_rows

if __name__ == '__main__':
    data = csv_reader("Lohnverrechnung.csv")
