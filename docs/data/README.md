# EnvGene: documentation sources

The originals behind the images the documentation embeds: the draw.io diagrams and the exported
data files.

This repository keeps them in [`docs/images/`](/docs/images/), where the pages already link to
them. Draw.io sources are the files named `*.drawio.png`, the draw.io document inside the PNG. To
change such a diagram, open the PNG in draw.io, edit it and export it back over the same file, so
every page that embeds it updates at once.

Keep one source per diagram, named like the image it produces (`deployment.drawio` exports
`deployment.png`). Export a new diagram into `docs/images/` and reference it from the page that
explains it, never from an index.
