```
               ░░┐            ▄▄▄       ▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄ 
              ░░┌┘           ▐░░░▌     ▐░░░░░░░░░▌ ▐░░░░░░░░░▌ ▐░░░░░░░░░▌
             ░░┌┘            ▐░░░▌     ▐░░░▛▀▀▀▀▀  ▐░░░▛▀▀▀▀▀  ▐░░░▛▀▀▀▀▀ 
 +━━+        └─┘ +━━+        ▐░░░▌     ▐░░░▌       ▐░░░▌       ▐░░░▌      
 ┃╳╳━━━━━━━+ +━+ ┃╳╳━━━━━━━+ ▐░░░▌     ▐░░░▙▄▄▄▄▄  ▐░░░▙▄▄▄▄▄  ▐░░░▙▄▄▄▄▄ 
 ┃╳╳┃      ┃ ┃╳┃ ┃╳╳┃      ┃ ▐░░░▌     ▐░░░░░░░░░▌ ▐░░░░░░░░░▌ ▐░░░░░░░░░▌
 ┃╳╳┃      ┃ ┃╳┃ ┃╳╳┃      ┃ ▐░░░▌     ▐░░░▛▀▀▀▀▀   ▀▀▀▀▀▜░░░▌  ▀▀▀▀▀▜░░░▌
 ┃╳╳━━━━━━━+ +━+ ┃╳╳━━━━━━━+ ▐░░░▌     ▐░░░▌             ▐░░░▌       ▐░░░▌
 ┃╳╳┃            ┃╳╳┃        ▟░░░▙▄▄▄▄▄▟░░░▙▄▄▄▄▄▄▄▄▄▄▄▄▄▟░░░▙▄▄▄▄▄▄▄▟░░░▌
 ┃╳╳┃            ┃╳╳┃       ▐░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▌
 +━━+            +━━+        ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ 

```

# `pipless`

`pipless` (pip LESS, as in "use it less") automagically creates and activates
virtual environments, installs packages dynamically, and keeps your project's
`requirements.txt` up-to-date by (re)generating it when the process exits.

No more must python developers go through the rote project lifecycle steps of

* Creating a virtual environment
* Activating it
* Manually updating the requirements.txt when it's realized that additional packages are needed
* Don't forget to run `pip freeze` to pin your requirements to specific versions!

## Usage

In most situations `pipless` can be used as a drop-in replacement for directly
using the python executable.

It can be used in three ways:

1. To run a separate python script:

![pipless running separate scripts](https://i.imgur.com/JRnMguh.gif)

2. To start an interactive python shell:

![pipless interactive python shell](https://i.imgur.com/JztPIQk.gif)

3. Directly imported and initialized in Python:

```python
import pipless
pipless.init(... opts ...)

import tabulate
```