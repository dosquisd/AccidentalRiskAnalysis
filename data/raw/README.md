# Raw Data

Fuente de los datos encontrados

1. `accidente-de-trafico-en-bogota-entre-2007-y-2017-geopoint.csv`: [https://transport.opendatasoft.com/explore/dataset/accidente-de-trafico-en-bogota-entre-2007-y-2017-geopoint/table/](https://transport.opendatasoft.com/explore/dataset/accidente-de-trafico-en-bogota-entre-2007-y-2017-geopoint/table/). Esta fue el dataset principal, y la base de todos los análisis que se hicieron
2. `vm_acc_via.csv`: [https://transport.opendatasoft.com/explore/dataset/vm_acc_via/table/](https://transport.opendatasoft.com/explore/dataset/vm_acc_via/table/). Este dataset realmente no se utilizó, se tuvo la intención, pero se decidió prescender de ella.
3. `poligonos-localidades.zip`: [https://transport.opendatasoft.com/explore/dataset/poligonos-localidad-2/information/](https://transport.opendatasoft.com/explore/dataset/poligonos-localidad-2/information/). El enlace original ya no existe, pero de los datos mantienen la misma estructura de este nuevo fuente. Estos datos fueron usado con bastante frecuencia para analizar y mostrar los datos con base a la localidad.
4. `bogota_osmnx.pkl`: [notebooks/013_points_maps.ipynb](../../notebooks/013_points_maps.ipynb). Se sacaron unos mapas utilizando [OSMnx](https://osmnx.readthedocs.io/en/stable/), y para no tener que cargar los datos continuamente, se utilizó [pickle](https://docs.python.org/3/library/pickle.html) para guardar estos datos y sea mucho más rápido su uso. En el dashboard principal no se utilizó el mapa generado.
