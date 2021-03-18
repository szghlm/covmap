# Interaktív térkép készítése

Az alábbi kis leírás egy egyszerű, interaktív [térkép](https://szghlm.github.io/covmap/) elkészítésének folyamatába enged betekintést, egy aktuális problémán keresztül,
kedvcsinálóként mindazok számára, akik némi Python tudással felvértezve ilyesmire adnák a fejüket. 
Gondolok itt elsősorban a DE-IK GI szakjának (aktuális vagy leendő) hallgatóira, hiszen az ő életükben várhatóan kiemelt helyet foglal majd el az adatokkal való munka. 

## Cél

A cél egy adott időszakra vonatkozó, összesített COVID-fertőzöttségi adatokat megjelenítése olyan formában, hogy első pillantásra lehessen látni azt, hogy 
mely településeket érintett jobban és melyeket kevésbé a fertőzés. Az érintettséget az esetszám és a lakosság hányadosaként fogjuk definiálni. 

_Megj.: A kimenetként kapott térképnek nem célja tájékoztatást adni az aktuális vírushelyzetről, a rendelkezésre álló adatok nem is adnak erre lehetőséget._

## Felhasznált adatok

### Covid19 adatok

Összesített COVID-fertőzöttségi adatok a 2020.03.04-2021.02.14. időszakra vonatkozóan, településenkénti bontásban.  

Az adatokat a K-monitor szerezte meg közérdekű adatigénylés keretében az Országos Tisztifőorvostól, 
majd az adatok elérhetőségét egy [facebook bejegyzésben](https://www.facebook.com/Kmonitor/posts/4022020954485411) megosztották a nyilvánossággal is. 
Az adatok kezelője a Nemzeti Népegészségügyi Központ. 

**Az adatok formátuma, felépítése**

A covid19 adatok táblázatos formában érhetőek el ([Google Sheets](https://docs.google.com/spreadsheets/d/1ConGRVdv8jocW8G1lhpLqbDVnYwibjP1xhQJ5qiP_Ew/edit#gid=1212454019)). 
A térkép előállításához a dokumentum 2. lapjnak (pontosvesszővel tagolt) csv formátumba mentett változatát használtam ("covid19.csv")
melynek 1. oszlopa tartalmazza a települések nevét, a 2. oszlopa a fertőzöttek számát. A fájl első sora az oszlopfejléceket tartalmazza.


### Térképi adatok

A térkép adatok forrásaként az [OpenStreetMap](https://wiki.openstreetmap.org/wiki/Main_Page) (későbbiekben OSM) szabad licencű térinformatikai adatbázist fogjuk használni. 


### Települések térképi koordinátáinak összegyűjtése

Az adatok térképen történő megjelenítése érdekében össze kell gyűjtenünk a covid19.csv fájlban szereplő települések földrajzi koordinátáit, melyet programból fogunk megtenni. 

Első lépésként készítünk egy függvényt, mely a város neve alapján visszaadja azok szélességi és hosszúsági koordinátáit:

```
import geopy
def __getLocation(city):
    locator = geopy.geocoders.Nominatim(user_agent="city2location")
    city = locator.geocode(city)
    return city.latitude, city.longitude
```

Az érdemi munkát, a településnév geokódolását az OSM-hez fejlesztett [Nominatim](https://geopy.readthedocs.io/en/stable/index.html?highlight=Nominatim#geopy.geocoders.Nominatim)
végzi el, mely képes az OSM referenciatáblázatából kikeresi a településhez tartozó földrajzi koordinátákat. A Nominatim egy kompromisszumos megoldás. Ingyenesen 
használhatjuk, cserébe viszont nem terhelhetjük túl a szolgáltatást, másodperncenként egy kérésünket fogja kiszolgálni. 

Majd írunk egy függvényt a covid19.csv (vagy azzal egyező felépítésű) fájlban szereplő adatok memóriába történő felolvasására is. A függvény az értékes sorokban 
szereplő adatokat -- megfelelő formára hozva -- bepakolja egy listába. 
A visszaadott listában (településnév, esetszám, népesség) felépítésű rendezett hármasok szerepelnek majd. 

```
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
```

A következő függvény felelős azért, hogy az előbbi függvény által előállított listát és a korábban megírt _\_\_getLocation()_ függvényt felhasználva
előállítson egy új listát, melyben a covid.csv-ben található adatok mellett már a települések földrajzi koordinátái is szerepelnek. A település nevéhez a 
biztonság kedvéért az országot is hozzáfűzzük, mert előfordulhat, hogy ugyanazon név több országban is előfordul.

```
import logging
logging.basicConfig(filename='info.log', encoding='utf-8', level=logging.DEBUG)

def __addLocation(datalst):
    lst = []
    for city, cases, pop in datalst:
        try:
           #logging.info(city) 
           lat, lon = __getLocation(city + ' Hungary')
           lst.append((city, cases, pop, lat, lon))
        except:
           logging.warning(f'problémás település: {city}') 
           
    return lst
```

A koordináták lekérdezése során előfordulhatnak hibák, például ha a _city_ paraméterben átadott településnév nem található az OSM referenciatáblázatában.
A ciklus belsejében álló kivételkezelő gondoskodik arról, hogy ilyen esetben se szakadjon meg a folyamat. A problémás településnevek naplózásra kerülnek. 

A kapott adatokat érdemes eltárolni, hogy a további részek fejlesztése során már ne kelljen újra és újra igénybe venni a Nominatim szolgáltatását. 
Az adatmentést a _\_\_writeLocations()_ függvény teszi majd kényelmessé.    

```
def __writeLocations(filename, datalist):
     with open(filename, mode = "w", encoding="utf-8") as f:
        f.write("city;cases;pop;lat;lon;\n")
        for city, cases, pop, lat, lon in datalist:
              f.write(f"{city};{cases};{pop};{lat};{lon};\n")
```

Végül írunk egy kis függvényt a konvertálási folyamat irányítására. Első paraméterként a covid19.csv-nek megfelelő felépítésű adatokat
várja, második paraméterként pedig annak a fájlnak a nevét, melybe az adatok térképi koordinátákkal kiegészített változatát
menti. 
```
def extendWithCoord(source_filename, dest_filename):
    datalist = __readCovidData(source_filename)
    datalist2 = __addLocation(datalist)
    __writeLocations(dest_filename, datalist2)
```

A teljes kód megtalálható a _city2locations.py_ fájlban.


 
### A térkép elkészítése

Annak érdekében, hogy a következő lépéseket könnyebb legyen követni, létrehozok egy osztályt az egy ponthoz tartozó 
információ (város neve, esetszám, népesség, térképi koordináták) tárolására. Az osztályban látható metódusok az adatok térképen történő megjelenítésénél kapnak majd szerepet. 

```
class DataPoint:
    def __init__(self, city, n_cases, population, lat, lon):
        self.city = city
        self.n_cases = n_cases
        self.population = population
        self.location = [lat, lon]
        print(self.city, self.location)

    def get_ncases_per_population(self):
        if self.population > 0:
            return self.n_cases/self.population
        return 0

    def __str__(self):
        return f"<b>{self.city}</b><br>" \
               f"esetszám: {self.n_cases}<br>" \
               f"népesség: {self.population}<br>" \
               f"eset/népesség: {self.get_ncases_per_population()*100:0.2f}%<br>"
```

Mivel az előző részeket úgy írtuk meg, hogy a megjelenítéshez szükséges adatok egy fájlba kerüljenek, ezért készítünk egy függvényt, 
mely képes felolvasni és DataPoint objektumokként egy listába pakolni a koordináttákkal kiegészített covid adatokat.  

```
def readData(filename):
    lst = []
    with open(filename, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader) # skip header
        for row in reader:
            if len(row) >= 5:
                lst.append(DataPoint(row[0], int(row[1]), int(row[2]), float(row[3]), float(row[4])))
    return lst
```

(Aki ismeri pl. a Pandas csomagot, bátran válasszon más megoldást a fentiek helyett.) 


Most már tényleg jöhet a térkép előállítása. A webes térképek esetében az interaktivitás lehetőségét (zoomolás, navigálás, pontok kijelölése, stb.)
általában JavaScript biztosítja. Mi egy open-source függvénykönyvtárat, a [Leafletet] fogjuk felhasználni. De semmi pánik, egy sor JavaScriptet
sem kell írnunk, a [Folium](https://python-visualization.github.io/folium/) Python modul legenerálja majd a szükséges részeket helyettünk.

A térkép létrehozását az alábbi függvény végzi el:
```
import folium as fl
import branca.colormap as cm

def createMap(data):
    map = fl.Map(location=[47.20, 19.50], tiles = 'cartodbpositron', zoom_start=8)

    maxCases = max(data, key=lambda d: d.get_ncases_per_population()).get_ncases_per_population()
    scale_factor_circle = 5000.0/maxCases # 5000 - max radius of city (in metre)

    colormap = cm.LinearColormap(colors=['yellow', 'green', 'blue', 'purple', 'red'], vmin=0, vmax=maxCases*100)
    map.add_child(colormap)

    for datapoint in data:
        if datapoint.location:
            nc = datapoint.get_ncases_per_population()

            fl.Circle(
                location = datapoint.location,
                tooltip = str(datapoint),
                radius = max(1, nc * scale_factor_circle),
                color=colormap( nc*100 ), 
                opacity=0.75,
                fill=True,
                fill_opacity=0.5).add_to(map)

    return map
```

Rögtön a függvény elején példányosítunk egy Map objektumot, 
meghatározva az alaptérképet, melyhez az adatokat kapcsolhatjuk. 
A _location_-nak átadott szélességi és hosszúsági koordináták és a nagyítás mértéke úgy van beállítva, hogy a térképen Magyarország legyen látható. 

A _tiles_ paraméter értéke határozza meg a csempekészletet. Nem, ez a szó itt nem a fürdőszobai csempére utal, hanem egy kis négyzet alakú, a térkép megfelelő részét tartalmazó
képre. Ezekből a csempékből áll majd elő a felhasználó által aktuálisan látható térképrész. A _tiles_ paraméter beállításánál figyeljün arra, hogy
az igényeinknek megfelelő [csempeszolgáltatást](https://python-visualization.github.io/folium/modules.html) vegyünk igénybe. 
A 'cartodbpositron' világos megjelenésű térképet eredményez majd, melyen jól látszanak majd a különféle színnel rajzolt körök. 



A függvény következő sorai biztosítják majd, hogy a vírusfertőzés mértékét jelölő körök mérete és színe megfelelő értékek között mozogjon. 
A _maxCases_ változóba a fertőzés által leginkább érintett településhez tartozó esetszám/lakosság érték kerül. 
A _scale_factor_circle_ értékét pedig arra fogjuk használni, hogy az esetszám/lakosság értékeket a [0; 5000] tartományba skálázzuk át, 
így egyetlen egy kör sem fog túl sokat kitakarni a térképből.

A _colormap_ egy színpalettát tartalmaz. A minimum és maximum értéket úgy állítsuk be, hogy igazodjon a szinezéshez felhasznált jellemző tartományához.
Esetünkben a térképen megjelenített körök mérete és színe is az esetszám/lakosság hányadostól függ majd. 
A színskála már használható, de a felhasználók számára is érdemes láthatóvá tenni, hogy könnyebben tudják értelmezni a színek jelentését. 
Erre szolgál a _map.add_child(colormap)_ függvényhívás.

Végül az _adat_ listát bejárva létrehozzuk a települések érintettségét jelző köröket. Az átlátszatlanság (opacity) állításával elérjük, hogy a kör alatti részek is láthatóak maradjanak valamennyire, 
ez segíti, hogy a térképen lévő településnevek a sok jelölő ellenére is olvashatóak maradjanak.
A _tooltip_ paraméternek átadjuk az adatponthoz tartozó leírást, így ha a felhasználó egy kör fölé mozgatja az egeret, megjelenik majd
egy kis szöveges "buborék", ami a település nevét és a településhez tartozó fertőzöttségi adatokat tartalmazza. 


A következő függvény címmel látja el a térképet, és elmenti a térképet a kívánt néven. Az eredmény egy böngészőben megjeleníthető HTML fájl lesz. 

def createHtml(map, dest_filename = 'map.html'):
    title_html = """<h3>COVID19 összesített esetszám településenként (2020.03.04-2021.02.14.-ig) </h3>
                    Az adatok forrása: https://docs.google.com/spreadsheets/d/1ConGRVdv8jocW8G1lhpLqbDVnYwibjP1xhQJ5qiP_Ew/edit#gid=1499258253 
                <br>"""

    map.get_root().html.add_child(fl.Element(title_html))
    map.save(dest_filename)


A nehezével már végeztünk, már csak fel kell használni a megírt függvényeket. Ha a koordinátákkal kiegészített állomány még nem létezik,
akkor az _extendWithCoord_ függvényt meghívva létrehozzuk azt. Majd meghívjuk az adatok beolvassáára szolgáló függvényt és 
a térképkészítőt, létrehozzuk a térképet tartalmazó weblapot, és elmentjük azt a kívnánt néven.  
 
source_original = "../data/covid19.csv"
source_with_city = "../data/data.csv"
if __name__ == '__main__':
    if not os.path.exists(source_with_city):
        cl.extendWithCoord(source_original, source_with_city)

    data = readData(source_with_city)
    map = createMap(data)
    createHtml(map, "index.html")

Jó szórakozást a saját térképed elkészítéséhez!


