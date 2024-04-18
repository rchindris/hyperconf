Creating Configuration Files
-------------------------

Configuration files are plain YAML files containing configuration
objects. HyperConf can load these files, check their structure against
defined configuration schemas, and validate values. Parsing the
configuration results in a custom Python dictionary that can be used
either by looking up string keys or by accessing using attribute
names.

Typically, a configuration file imports schema definitions from schema
files. It then can contain any number of configuration object
declarations.

The `use` directive
-------------------

Schemas need to be defined separately of configuration files and be
included in the configuration file using an `use` directive. This
encourages the reuse of configuration definition files.  `use`
directives can appear anywhere at the top level in the configuration
or schema definition files.

The correct form of an `use` directive is::

  use: file_path

where `file_path` is the relative or absolute path of a schema YAML
file. The extension can be ommited in which case the '.yaml' suffix is
appended automatically.

Schema Definition File Lookup
-------------------------

HyperConf attempts to load referenced definition files that are
specified using file paths. The specified path can be an absolute
path, relative path, or a file name. When only a file name is
specified, the current working directory is used.

Examples:

- Load the `ships.yaml` file from the `../defs` directory.
  ::
  
    use: ../defs/ships

- Load the `ships.yaml` file from an absolute path.
  ::
  
    use: /home/user/ships

- Load from the current directory.
  ::
  
    use: ships

Package Resource Lookup
^^^^^^^^^^^^^^^^^^^^^^

If the file is not found in the specified path, `HyperConf` looks up the
path as a resource in one of the packages from the configuration
definition lookup path. When searching for a configuration definition
file in a package, the path is relative to the package root.

To register a package in the lookup path, use
`ConfigDefs.add_package`, as shown in the following example:

.. code-block:: python

    from hyperconf import ConfigDefs

    # Register the 'my_package' Python package as a configuration definition source.
    ConfigDefs.add_package('my_package')


Declaring Objects
----------------

An object declaration assigns an alias to configuration values. The
name specifies the configuration definition to use and the YAML object
definition needs conform to the structure specified by the
configuration. 

Object Names
^^^^^^^^^^^^

An object name can be:

 - a configuration definition type name, in which case only one
   declaration for that configuration definition is possible in a
   configuration file. In the following example:::

     use: ships

     ship:
       captain: Pike
       ...

     ship:
       captain: Kirk
       ...

     ship:
       captain: Picard
       ...

   three objects with name and type `ship` are defined and the result
   is that the last declaration shadows the previous two declarations
   since they have the same name.
   
 - an inline type alias, defining an unique name for the object.  A
   type alias has the form `object_id=definition_name` as in the
   following example:::
     use: ships
     
     enterprise=ship:
       ...

     stargazer=ship:
       ...

   In this example two distinct `ship` objects were defined, each one
   with its configuration values.
   
