# musicxml2hum
MusicXML to Humdrum converter

## About this fork

Fork of [craigsapp/musicxml2hum](https://github.com/craigsapp/musicxml2hum) with fixes for several crashes and conversion bugs encountered on real-world MusicXML input, including:

- invalid spine structure for tempo directions in invisible pickup measures
- bracket directions incorrectly converted to `*lig`/`*Xlig` markers
- slice selection and duplicate tie markers in humlib
- `*(a)` text annotations being interpreted as Humdrum syntax

The `humlib` and `pugixml` sources are vendored directly in this repo (upstream fetches them via a `download.sh` script) so the fixes live alongside the code they patch rather than as out-of-tree diffs.

## Compiling ##

To compile the command-line version of musicxml2hum2, type:

```bash
	make
```

This will create the executable `./bin/musicxml2hum`.  

To install the executable in `/usr/local/bin`, then type:

```bash
make install
```

musicxml2hum is also included in [humlib](http://humlib.humdrum.org).


