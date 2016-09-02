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

`pipless` (pip LESS, as in "use it less frequently") automagically creates and activates
virtual environments, installs packages dynamically, and keeps your project's
`requirements.txt` up-to-date by (re)generating it when the process exits.

No more must python developers go through the rote project lifecycle steps of

* Creating a virtual environment
* Activating it
* Manually updating the requirements.txt when it's realized that additional packages are needed
* Not forgetting to run `pip freeze` to pin your requirements to specific versions!

Not only does it perform all the above steps for you, it does it *WITHOUT REQUIRING
ANY CODE CHANGES*

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

## Trying it out

`pipless` is currently under development, with most of the working code
living in the develop branch; it is not ready to be released/made available
through PyPI. If you'd like to give it a try locally without fully installing
it, the commands below should help get you setup:

```
cd /tmp
git clone https://github.com/d0c-s4vage/pipless.git
cd pipless
git checkout develop
PATH="/tmp/pipless/scripts:$PATH"
PYTHONPATH="/tmp/pipless:$PYTHONPATH"
pipless --help
```