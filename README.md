# Eclipse-and-Qt-Creator-Files-for-UE4

This is a quick one-off script for generating the files to evaluate Eclipse CDT and QT Creator 5 as an alternative to
Visual Studio 2019 for Unreal Engine 4 development on Windows.

Requires Python 3.

## How to use this

1. Drop in the same directory as sln and uproject.

2. Double click or execute from the command line to generate:

- Source/EclipsePathsAndSymbols.xml
- Source/{project_name}.pro
- Source/includes.pri
- Source/defines.pri

3. Set up your projects:

- Qt: Bits and pieces
  from [this tutorial](https://forums.unrealengine.com/t/tool-tut-win-unreal-qt-creator-project-generator-v0-3/21391)
  work, a few menus were moved around since then.

- Eclipse:

  a) Install Eclipse CDT

  b) [Set up Cygwin](https://www.eclipse.org/4diac/documentation/html/installation/cygwin.html)

  c) Create a Makefile Project with Existing Code (Cygwin GCC, Language: C++), pick your source directory.

  d) Properties -> C/C++ General -> Paths and Symbols -> GNU C++ -> Import

## Evaluation results

These are my experiences as of June 2021. I looked at responsiveness and navigation capabilities.Tested on an i7-10875H
/ 32GB of memory / SSD.

I purposefully ignore paid solutions here. I did not look at completion and refactoring capabilities.

TLDR: I wasn't able to get either Eclipse, or Qt Creator to work properly in the time I set aside for this.

### Visual Studio

In my experience:

- It keeps reindexing all the time.
- It's slow to navigate and find usages (slow=multiple seconds).

```
IntelliSense operation in progress...
```

### Qt Creator

Similar experience to Visual Studio:

- Reindexes from the beginning when opening a project.
- After it's done indexing, it still isn't fully functional,
  (e.g. when opening a new project file, it's grayed out for multiple seconds)

Promising features:

- It builds an index of some kind up front in a finite amount of time.
- Seems more lightweight than Visual Studio 2019.

### Eclipse CDT

The way Eclipse CDT works, it wouldn't reindex needlessly once the index was built. In my experience, it has vastly
superior navigation capabilities UX-wise to Visual Studio
(instant Navigate, Find Usages, Call Hierarchy), though these require the index to be built properly (see below)

I was unsuccessful in getting it to work:

#### It lacks the scalability to index the entire engine code

a) The indexer is slow and hard to debug

  ```
  [1,623,383,665,339] Parsed GroupedSpriteSceneProxy.cpp: 4533 ms - parse failure. Ambiguity resolution: 1940 ms
  ```

b) The indexer is single-threaded, see [Bug 351659](https://bugs.eclipse.org/bugs/show_bug.cgi?id=351659)

c) If the entire engine code is included, it errors out on memory very early (~1-3% indexed, tested up to 16GB heap
space)

  ```
  java.lang.OutOfMemoryError: Java heap space
  ```

To test this scenario, add engine code (Properties -> C/C++ General -> Paths and Symbols -> Source Location: Engine
folder, e.g.

  ```
  C:\Program Files\Epic Games\UE_4.26\Engine
  ```

#### It has trouble with the widespread use of macros in engine code

a) Codan seems to ignore variadic macros like UCLASS sometimes reporting

```
Syntax error: [X] could not be resolved
```

despite "Go To Definition" working. Similar to [this](https://www.eclipse.org/forums/index.php/t/1086391/), but the
resolution doesn't work. It will report this error in one file, but not another file next to it.

I used a workaround to define these variadic macros at the project level.

b) It cannot handle generated code macros like GENERATED_BODY, it seems to confuse them across translation units.

I don't see an easy workaround, since the generated methods are very common.

## Acknowledgements

- Unreal® is a trademark or registered trademark of Epic Games, Inc. in the United States of America and elsewhere.

- Qt is a trademark of The Qt Company Ltd in Finland and/or other countries worldwide.

- IntelliSense and Visual Studio are registered trademarks of Microsoft Corporation in the United States and/or other
  countries.

## License

```
MIT License

Copyright (c) 2021 Matt Garstka

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
