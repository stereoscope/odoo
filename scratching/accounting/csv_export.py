import csv_import
import csv
import json
import os

columns = ["Journal","Nummer","Referenz","Buchungszeilen/Konto","Buchungszeilen/Kostenrechnung","Buchungszeilen/Soll","Buchungszeilen/Haben"]

def run():
    for file in os.listdir("sources"):
        if file.startswith("."):
            continue

        output_file = f"Lohnverrechnung_{os.path.basename(file)}_.csv"
        output = os.path.join("output", output_file)
        input_file = f"sources/{file}"
        export(input_file, output)

def export(source_file, output_file):
    journal = "Miscellaneous Operations"
    number = "Nummer TEST"
    reference = "Referenz TEST"

    data = csv_import.csv_reader(source_file)

    records = []

    curr_row = 0
    for it in data:
        if curr_row == 0:
            row = {
                "Journal": journal,
                "Nummer": number,
                "Referenz": reference,
            }
        else:
            row = {
                "Journal": "",
                "Nummer": "",
                "Referenz": "",
            }

        if it['soll'] != 0 or it['haben'] != 0:
            rec = {
                "Buchungszeilen/Konto": it["konto"],
                "Buchungszeilen/Kostenrechnung": json.dumps(it["kostenstelle"]) if it["kostenstelle"] else "",
                "Buchungszeilen/Soll": it["soll"] * -1 if it["soll"] < 0 else it["soll"],
                "Buchungszeilen/Haben": it["haben"] * -1 if it["haben"] < 0 else it["haben"],
            }
            records.append(row | rec)

        curr_row += 1

    ordered_records = sorted(records, key=lambda d: d['Buchungszeilen/Kostenrechnung'])

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        writer.writeheader()  # first row
        writer.writerows(ordered_records)


if __name__ == "__main__":
    run()