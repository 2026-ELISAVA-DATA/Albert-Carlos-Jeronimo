Scrapping de twitter
Windows : 
chrome --remote-debugging-port=9222 --user-data-dir="/ruta/tu_perfil_chrome": 

Para Mac: open -na "Google Chrome" --args --user-data-dir="/Users/koli/Library/Application Support/Google/Chrome/Default"

Version que funciona:
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="/Users/koli/Library/Application Support/Google/Chrome/Default"

Mejor version, paa que seguro me abra el chrome en local, y iniciar como invitado:
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug"


Despues de cada scrap de twitter:

Also make sure you **fully quit Chrome first** before running the open command. If Chrome is already running it will just open a new window in the existing process without the debugging flag:

Hacer bash

```bash
pkill -a -i "Google Chrome"
# wait 2 seconds then
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug"
```

Otros setups:

```bash
pkill -a -i "Google Chrome"

```
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --no-first-run --no-default-browser-check --user-data-dir="/tmp/chrome_scraping" "about:blank"
```

```bash
curl http://localhost:9222/json
```

cd /Users/koli/Documents/ELISAVA/DATA/Albert-Carlos-Jeronimo/scrapping_twitter
python3 scrapp_twitter_V3.py