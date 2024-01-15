Configuration Schema Definition
===============================


By defining a configuration object schema, you gain control over the structure of those configuration objects. This involves specifying the options and their types, along with setting value validation rules and string-to-value conversion.

The `use` directive
-------------------

Schemas need to be defined separately of configuration files and be included in the configuration
file using an `use` directive. This encourages the reuse of configuration definition files.
`use` directives can appear anywhere at the top level in the configuration or schema definition files.

The correct form of an `use` directive is::

  use: file_path

where `file_path` is the relative or absolute path of a schema YAML file. The extension can be
ommited in which case the '.yaml' suffix is appended automatically.

Defining an Object
------------------

In a configuration schema, any top-level YAML node, excluding the use node, is considered to define an object type. The YAML key serves as the type name, and the node contents are interpreted as follows:

  - If the node is of type string, the node value specifies the type name of this object and needs to be previously defined. Example::
      
      ...
      threshold: percent
      ...

  - If the node is of type dictionary, it is treated as a complex type definition. Complex type definitions can include:
    
    - `typename`: Specifies the name of the type.
      
    - `required`: A boolean flag indicating whether instances of this type are required or not.
      
    - `validator`: A valid Python expression that checks values of this type.
      
    - `converter`: A valid Python expression that converts strings to type values.

      
In addition to the above, any other property specified is regarded as an option definition. An option definition node cannot contain keys other than those mentioned above; in other words, nesting type definitions is forbidden.

The following example is an incorrectly defined object type::

      incorrect_def:
        valid_option: str
        another_valid_option:
          type: int
          validator: 'int(hval) > 3'
        invalid_option:
          nested_opt: int

In this case the `invalid_option` option attempts to nest another type definition. The correct way of doing this is::

       was_nested: str
       correct_def:
        valid_option: str
        another_valid_option:
          type: int
          validator: 'int(hval) > 3'
        now_valid_option: was_nested


Validating and Converting Values
--------------------------------

`HyperConf` definitions can specify validation and value conversion rules. A validation rule must be a valid Python expression that results in either a boolean value or a tuple containing a boolean value and a string. In the latter case, the string represents the error message to be reported back to the user if the validation fails.

The validation expression can utilize the following references:

  - `hval`: the value found in the configuration file, as a string.
  - `htype`: the configuration type of the declaration.

In addition to these references, the code can make use of the modules `re`, `math` and `pathlib`.
For converter expressions, the expression converts a string value to the respective type. The same conditions apply during evaluation as for validator expressions.

Builtin Types
--------------

Schema definition and configuration declaration files can access the following predefined configuration types:

  - str: alias for a string value.
    
  - int: validates and converts integer values.

  - pos_int: validates and converts positive integers.

  - float: validates and converts real numbers.

  - percent: validates and converts float values between 0 and 1.

  - path: alias for string values that point to a file or directory.

(more to come)
  
