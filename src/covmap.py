import branca.colormap as cm
import folium as fl
import csv
import city2location as cl
import os, sys

#https://docs.google.com/spreadsheets/d/1ConGRVdv8jocW8G1lhpLqbDVnYwibjP1xhQJ5qiP_Ew/edit#gid=1499258253

source_original = "../data/COVID19_településenként_2021.02.14.csv"
source_with_city = "../data/data.csv"

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


def readData(filename):
    lst = []
    with open(filename, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader) # skip header
        for row in reader:
            if len(row) >= 5:
                lst.append(DataPoint(row[0], int(row[1]), int(row[2]), float(row[3]), float(row[4])))
    return lst


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
                color=colormap( nc*100 ), # scale_factor_color
                opacity=0.75,
                fill=True,
                fill_opacity=0.5).add_to(map)

    return map


def createHtml(map):
    title_html = """<h3>COVID19 összesített esetszám településenként (2020.03.04-2021.02.14.-ig) </h3>
                    Az adatok forrása: https://docs.google.com/spreadsheets/d/1ConGRVdv8jocW8G1lhpLqbDVnYwibjP1xhQJ5qiP_Ew/edit#gid=1499258253 
                <br>"""

    map.get_root().html.add_child(fl.Element(title_html))
    map.save('osm.html')

 #   test = fl.Html('', script=True)
 #   popup = fl.Popup(test, max_width=2500)


if __name__ == '__main__':
    if not os.path.exists(source_with_city):
        cl.extendWithCoord(source_original, source_with_city)

    data = readData(source_with_city)
    map = createMap(data)
    createHtml(map)




#fl.Marker(location="", popup="", tooltip="")