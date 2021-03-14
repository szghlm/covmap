import csv
import geopy

# for test
__source = "COVID19_településenként_2021.02.14.csv"

def __getLocation(city):
    locator = geopy.geocoders.Nominatim(user_agent="city2location")
    city = locator.geocode(city)
    return city.latitude, city.longitude

def __readCovidData(filename):
    lst = []
    with open(filename, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader)  # skip header
        for row in reader:
            if len(row) > 0 and row[0].strip() != "":
               # telepules, esetszam, nepesseg
               lst.append( (row[0], int(row[1].replace(" ", "")), int(row[2].replace(" ","") )) )

    return lst

def __addLocation(datalst):
    lst = []
    for city, cases, pop in datalst:
        try:
           print(city)
           lat, lon = __getLocation(city)
           lst.append((city, cases, pop, lat, lon))
        except:
           print("problémás város:", city)
    return lst

def __writeLocations(filename, datalist):
     with open(filename, mode = "w", encoding="utf-8") as f:
        f.write("city;cases;pop;lat;lon;\n")
        for city, cases, pop, lat, lon in datalist:
              f.write(f"{city};{cases};{pop};{lat};{lon};\n")

def extendWithCoord(source_filename, dest_filename):
    datalist = __readCovidData(source_filename)
    datalist2 = __addLocation(datalist)
    __writeLocations(dest_filename, datalist2)

if __name__ ==  "__main__":
    extendWithCoord()

#fl.Marker(location="", popup="", tooltip="")