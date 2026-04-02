La app va a permitir un flujo con el que renombrar juegos y saves a la vez (es necesario que tengan el mismo nombre), eliminemos duplicados, organicemos todos los archivos en sus correspondientes carpetas...

En principio, tenemos una estructura de pestañas en el lateral izquierdo, donde, dependiendo de una selección arriba, trabajaremos en la misma feature sobre un dispositivo (PC), otro (consola android) o los dos (Sistema completo )

Las pestañas laterales tienen las siguientes features: 

- **inicio**: Nos muestra datos generales (estadísticas, número de juegos, juegos por consola...) en ambos dispositivos.
Además, aquí informamos al sistema con las rutas de juegos en PC y Consola Android. Además, aquí podemos lanzar la función scan

- **Juegos**: Muestra la lista de juegos, permitiendo ordenarlos por medio de desplegables (consola, año...)

- **Organizar**: permite renombrar juegos siguiendo su título canónico de los catalogs. ahora mismo, si dos juegos piden el mismo nombre, da un problema (la estrategia de renombrado es meter _1 o _2, pero no me gusta). Mi idea es que en esos casos, eliminemos uno de los dos, a ser posible, el que no tenga logros en Retro achievements

- **Duplicados**: Detecta automáticamente juegos duplicados y los elimina, quedándose, a ser posible, con la versión con logros

- **Assets**: muestra metadatos, carátulas y movidas varias

- **Colección**: en verdad es un poco igual que juegos, y justo estoy pensando que deberíamos quitarla... aunque no sé, quizá podemos meter aquí algún metadato más (tiempo de juego? podríamos incluso sincronizar logros? eso podría molar)

------------------------------SYNC--------------------------------
Aquí tenemos la chicha,  lo complejo. 
- **Cloud**: La idea de esta pestaña es dar datos sobre los distintos saves, y sincronizarlos con una nube (idealmente Dropbox)
    -*Problema*: hay que meter RCLONE y termux, y no tengo ni idea de cómo tratarlos (según claude, era la opción más válida)
- **Cable sync**: sirve para sincronizar conectando la anbernic por cable, ya que los juegos ocupan muchísimo más espacio. para hacer esto, es necesario instalar ADB, dentro de las herramientas de desarrollo de android, aunque es más fácil conectar la tarjeta SD directamente, ya que android no tiene que meter mano.
    *Problema*: PSX y PS2 (al menos) usan una ruta preconfigurada que va al almacenamiento interno de la consola, además es una ruta oculta, creo. No sé si tendremos acceso a ello, o estas dos consolas (las más importantes T.T) se quedarán sin sync de saves
- **Anbernic**: la puta hostia (si funciona bien, aun no la probé). la gracia de esto es, entrar desde la anbernic en retro vault y seguir un proceso muy guiado con el que evitar teclear en pantalla táctil

----------------------------Herramientas--------------------------
Tiene un problema que aún no he sido capaz de arreglar, y es que oculta el menú lateral de pestañas en algunas de estas pestañas.
- **tools**: Tiene distintas herramientas de las cuales no tengo muy claro que todas funcionen genial, y son:
    - Analizar biblioteca (busca cosas fuera de su carpeta)
    - Saves huerfanos: te avisa si hay saves sin juego 
    - Health check: detecta archivos corruptos
    - Roms no identificadas: busca en las carpetas de cada juego, y te dice qué archivos no aparecen en los catalogos (.dat)
    - Retroachievements: comprueba qué juegos NO tienen logros en tu versión, pero sí en otra, y te enseña el link de retroachievements para que compruebes cuál es y la descargues
    - Informe de biblioteca: Saca un informe en html con todo lo descubierto
    - Exportar pegasus metadata (crea un archivo para Pegasus frontend)
    - Limpieza de archivos no relacionados con gaming: se carga todo lo que no sea gaming dentro de las carpetas (aunque quizá podría crear una carpeta "basura" para comprobar esos archivos)
    - Estructura de biblioteca: Crea la estructura de carpetas en las rutas de PC y consola android (Comprueba library-structure)
- **formatos**: diferentes herramientas para cambiar de formato juegos
- **Scraper**: scrapea los metadatos de juegos en la web screenscraper (valoraciones, descripción, genero... etc, incluso carátulas) y las mete en una carpeta que hemos configurado para que el frontend ES-DE haga uso de ello (usando la función: crear gamelist.xml)
- **Inbox**: coge los juegos de la carpeta inbox, comprueba en los catalogs de qué plataforma son, y los mueve a su carpeta correspondiente

en la pestaña lateral abajo, faltarían solo modo tv y ajustes
ajustes, sobre todo, sirve para configurar las rutas de distintas cosillas, y meter configuraciones concretas (como por ejemplo, user y password)
Ahora mismo te permite también meter claves de developer en cosas, pero bueno, entiendo que eso habría que modificarlo si esto nos diera por sacarlo "público"


--------------PROBLEMAS---------------
- Creo que no tenemos todos los posibles catalogs, y faltan por bajar

- habría que simplificar el proceso. Me parecería bastante elegante que se hiciera todo de una, y luego dar al user la opción de ir pasando por las distintas tabs explicando los cambios que van a hacerse, y que él decida (o no, y que él se fíe)

- Hay que recomprobar que los emuladores de la consola y los que usamos en PC sean el mismo, o guarden los saves y savestates en un mismo sitio

- en el informe de juegos con logros en **RETROACHIEVEMENTS**, molaria infinito conseguir una manera de meter un botón "copiar link de descarga" por juego, ya que Jdownloader pone esos links directamente a descargar.
probablemente poner un llm en local para que añadiera el link dentro de los propios catalogs sería costoso, y fallaría, pero si eso funcionara, me haría increíblemente feliz :P

------------FUTURO-----------
- Si esto queda medio chulo, podria molar hacerlo un instalador para poder tener el programa activo, si por ejemplo tengo un periodo largo de descargar nuevas ROMS. 

- podría integrarse con ES-DE y crear sus archivos de configuración porque creo que son un coñazo de hacer (a mí me los ha configurado la IA porque eran terribles)

- Los juegos de consolas arcade me estan costando que te cagas: no tengo muy claro cómo hacerlos, cuál es su emulador... hay que darle una vuelta (y probablemente, eso más que a nivel programación, sea a nivel config)
