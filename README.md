# painterly-rendering
A Python 3 script to allow you to render images as if they were painted. Loosely follows this [SIGGRAPH paper](https://mrl.nyu.edu/publications/painterly98/hertzmann-siggraph98.pdf).

## Installation

The dependencies are:
```
pycairo==1.10.0
numpy==1.11.1
scipy==0.18.1
Pillow==4.0.0
```

You can install them by running:
`pip install -r requirements.txt`

## Usage

Typical usage may look something like this.

`$ python painterly-rendering.py -i test-images/haruhi.png -q high`

You can use the `-h` option to see the built-in help.

## Examples

`$ python painterly-rendering.py -i test-images/haruhi.png -q high -l`

![Source Haruhi Compared to Painterly Haruhi](./examples/layers_example.png)

`$ python painterly-rendering.py -i test-images/mountain.jpg`

![Source Mountains Compared to Painterly Mountains](./examples/mountain_comparison.png)

`$ python painterly-rendering.py -i test-images/flower.jpg`

![Source Flowers Compared to Painterly Flowers](./examples/flower_comparison.png)

`$ python painterly-rendering.py -i test-images/ross.jpg -q high`

![Source Bob Ross Painting Compared to Painterly Bob Ross Painting](./examples/ross_comparison.png)
