import re
import sys
import textwrap
import unicodedata

class AugurApiParser:
  def __init__(self):
    self._class_name = None
    self._class_type = 'Object'
    self._properties = dict()

  def parse_class(self, input):
    process_properties = False
    for i, line in enumerate(input):
      if i == 0:
        self._class_name = (line.rstrip()).split()[0]
      elif i == 2 and len(line) > 2 and 'enum' in line:
        self._class_type = 'Enum'
      elif process_properties and len(line) > 2:
        property_name, property_type, *property_description = line.split()
        if self._class_type is not 'Enum':
          property_name = self.camel_case_to_snake_case(property_name)
        properties_dict = {
          'type': property_type.strip('()').replace('|', ' or '),
          'desc': ' '.join(property_description)}
        self._properties.update({property_name: properties_dict})
      if line.startswith('Properties:'):
        process_properties = True

  def build_constructor(self):
    # Add Enum import if needed.
    if self._class_type is 'Enum':
      class_name = []
      for x in self._class_name.split('_'):
        class_name.append(x.capitalize())
      self._class_name = ''.join(class_name)
      constructor_list = [
        'from enum import Enum, auto\n\n',
        'class {}(Enum):\n'.format(self._class_name)
      ]
    else:
      constructor_list = [
        'class {}:\n'.format(self._class_name),
        'def __init__(self, {}):\n'.format(
          ', '.join([x for x in self._properties.keys()])),
        ['self._{0} = {0}'.format(x) for x in self._properties.keys()]
      ]
    return constructor_list

  def build_getters(self):
    if self._class_type is not 'Enum':
      getters_list = []
      for prop, values in self._properties.items():
        property_getter = [
          '@property',
          'def {}(self):'.format(prop),
          '{}{}'.format('\'' * 3, values['desc']),
          'Returns {}'.format(values['type']),
          '{}'.format('\'' * 3),
          'return self._{}\n\n'.format(prop)
        ]
        getters_list.append(property_getter)
      return getters_list

  def add_formatting(self, constructor, getter):
    textwrapper = textwrap.TextWrapper(width=80, subsequent_indent=' ' * 2)
    formatted_string = []
    if self._class_type is 'Enum':
      formatted_string.append(''.join(constructor))
      textwrapper.initial_indent = ' ' * 2
      textwrapper.subsequent_indent = ' ' * 6
      for x in self._properties:
        formatted_string.append(
          textwrapper.fill('{} = auto()'.format(x)) + '\n')
    else:
      # Add formatting for constructor definition.
      formatted_string.append(constructor[0])
      textwrapper.initial_indent = ' ' * 2
      textwrapper.subsequent_indent = ' ' * 6
      formatted_string.append(textwrapper.fill(constructor[1]))
      formatted_string.append('\n')
      # Add formatting for assigning constructor defaults.
      textwrapper.initial_indent = ' ' * 4
      textwrapper.subsequent_indent = ' ' * 4
      [formatted_string.append(
        textwrapper.fill(x) + '\n') for x in constructor[2]]
      # Add formatting for property getters.
      textwrapper.initial_indent = ' ' * 4
      textwrapper.subsequent_indent = ' ' * 4
      for x in getter:
        formatted_string.append('\n')
        for index, y in enumerate(x):
          if index == 0 or index == 1:
            textwrapper.initial_indent = ' ' * 2
            textwrapper.subsequent_indent = ' ' * 2
          else:
            textwrapper.initial_indent = ' ' * 4
            textwrapper.subsequent_indent = ' ' * 4
          if index == 3:
            formatted_string.append('\n')
          formatted_string.append(textwrapper.fill(y) + '\n')
    formatted_string = ''.join(formatted_string)
    formatted_string = self.replace_non_ascii(formatted_string)
    formatted_string = self.replace_with_python_types(formatted_string)
    return formatted_string

  def replace_non_ascii(self, text):
    ascii_map = [
      (u'\u2018', '\''),
      (u'\u2019', '\''),
      (u'\u201b', '\''),
      (u'\u201c', '\"'),
      (u'\u201d', '\"'),
      (u'\u201f', '\"')
    ]
    for unicode_char, replace_char in ascii_map:
      text = text.replace(unicode_char, replace_char)
    return text

  def replace_with_python_types(self, text):
    python_types = [
      ('string', 'str'),
      ('boolean', 'bool'),
      ('null', 'None'),
      ('Array.', 'list'),
      ('number', 'int'),
      ('function', 'callback')
    ]
    for ts_types, py_types in python_types:
      text = text.replace(ts_types, py_types)
    return text

  def camel_case_to_snake_case(self, text):
    text_part = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text_part).lower()

if __name__ == '__main__':
  augur_api_parser = AugurApiParser()
  augur_api_parser.parse_class(sys.stdin)
  formatted_string = augur_api_parser.add_formatting(
    augur_api_parser.build_constructor(),
    augur_api_parser.build_getters())
  print(formatted_string)
