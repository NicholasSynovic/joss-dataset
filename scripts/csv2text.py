import csv
import pathlib

p: pathlib.Path = pathlib.Path("dfVulFixVul.csv")

with p.open() as csvfile:
    reader = csv.DictReader(csvfile)
    for r in reader:
        print(r["codeLink"])
