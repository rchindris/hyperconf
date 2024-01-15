Quick Start
===========

Let's get started quickly! The instructions assume the use of `Poetry`. However, feel free to adapt them to your preferred dependency management tool, whether it's `Pipenv` or a straightforward `virtualenv`.

Firstly, grab the `hyperconf` library directly from `PyPI`::

  poetry add hyperconf


Make sure to execute this command in the same directory as your `pyproject.toml` file for your project. This command adds HyperConf as a dependency and installs the Python package into your project's virtual environment. If you're not using a virtual environment management tool, consider doing so – it will make your life much easier.

Now, let's define configuration objects that your code can comprehend. Let's imagine we're coding a simple Star Trek simulator that expects certain properties for spaceships to be specified in the configuration. Create a definition file named `ships.yaml`::

  # Spaceship Configuration Schema
  ship_type:
    type: str
    validator: hval.isalpha()
    required: true

  shipcolor:
    type: str
    validator: hval.lower() in ['red', 'blue', 'green', 'yellow', 'gray']
    required: true

  enginepower:
    type: int
    validator: 100 <= hval <= 1000
    required: true

  shieldlevel:
    type: percent
    required: true

  ship:
    captain: str
    crew:
      type: int
      validator: hval > 0
    class: shiptype
    color: shipcolor
    shields: shieldlevel
    engines: enginepower

In this file, we've defined what an object of type `ship` should look like. It needs a captain, engine power level, shield level, and other properties. Note that the `ship` object is composed of different other object types that were defined separately. The HyperConf schema definition parser does not allow nesting type definitions; you need to follow this principle: define the objects from bottom up and compose more complex objects using previously defined objects.

We're now ready to parse the first configuration using `HyperConf`. Create a `simulator.yaml` file that references the definitions from `ships.yaml`::
  
  use: ships

  ncc1701=ship:
    captain: James T. Kirk
    crew: 203
    class: constitution
    color: gray
    shields: 1.0
    engines: 900

This file contains configuration objects declarations. It starts by loading the object definitions from `ships.yaml` and then proceeds to create a configuration object of type `ship`. Note the notation used to specify the object key: `ncc1701=ship`. This declares the alias `ncc1701` for an object of type `ship` and is useful when having multiple objects of the same type. If you have only one ship instance, the name can be the type name.

Next, all that's left to do is to load and validate the configuration::
  
  from hyperconf import HyperConfig

  config = HyperConfig.load_yaml("simulator.yaml")
  print(config.ncc1701.captain)

Any configuration rule violations will be checked by `load_yaml` and relevant errors will be thrown - along with best-effort suggestions on how to correct them, ensuring that after the configuration is parsed you can safely use the values.
