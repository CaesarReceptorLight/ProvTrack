# ProvTrack
A module in CAESAR to visualize the complete path of a scientific experiment.

**Requirements**

* OMERO server. Check the guideliness to install OMERO [here](https://github.com/CaesarReceptorLight/openmicroscopy) 
* Install the third party libraries.
  * [Node.js](https://nodejs.org)

**Installation**

1.	Copy the folder 'ProvTrack' to:
```
    /home/omero/OMERO.server/lib/python/omeroweb/
```

2.	Add ProvTrack to the known web apps
```
    /home/omero/OMERO.server/bin/omero config append omero.web.apps '"ProvTrack"'
```

3.	Add the ProvTrack plugin to the list of top links plugins
```
   /home/omero/OMERO.server/bin/omero config append omero.web.ui.top_links '["ProvTrack", "provtrack", {"target": "new
", "title": "Provenance Tracking of Scientific Experiments"}]' 
```
4.  Restart the web server
```
    /home/omero/OMERO.server/bin/omero web restart
```
Publication
-----------
* [The Story of an Experiment: A Provenance-based Semantic Approach towards Research Reproducibility](http://ceur-ws.org/Vol-2275/paper2.pdf), Sheeba Samuel, Kathrin Groeneveld, Frank Taubert, Daniel Walther, Tom Kache, Teresa Langenstück, Birgitta König-Ries, H Martin Bücker, and Christoph Biskup, SWAT4LS 2018.



