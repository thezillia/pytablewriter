# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import six
from dataproperty import DataProperty, DefaultValue
from typepy import StrictLevel, Typecode

from ...._converter import strip_quote
from ...._function import quote_datetime_formatter
from ....sanitizer import sanitize_js_var_name
from .._common import bool_to_str
from ._sourcecode import SourceCodeTableWriter


def js_datetime_formatter(value):
    try:
        return 'new Date("{:s}")'.format(value.strftime(DefaultValue.DATETIME_FORMAT))
    except ValueError:
        # the datetime strftime() methods require year >= 1900
        return 'new Date("{}")'.format(value)


class JavaScriptTableWriter(SourceCodeTableWriter):
    """
    A table writer for class JavaScript format.

        :Example:
            :ref:`example-js-table-writer`

    .. py:attribute:: variable_declaration

        JavaScript variable declarations type.
        The value must be either ``"var"``, ``"let"`` or ``"const"``.
        Defaults to ``"const"``.

    .. py:method:: write_table

        |write_table| with JavaScript format.
        The tabular data are written as a nested list variable definition.

        :raises pytablewriter.EmptyTableNameError:
            If the |table_name| is empty.
        :raises pytablewriter.EmptyTableDataError:
            If the |headers| and the |value_matrix| is empty.
        :Example:
            :ref:`example-js-table-writer`

        .. note::
            Specific values in the tabular data are converted when writing:

            - |None|: written as ``null``
            - |inf|: written as ``Infinity``
            - |nan|: written as ``NaN``
            - |datetime| instances determined by |is_datetime_instance_formatting| attribute:
                - |True|: written as `dateutil.parser <https://dateutil.readthedocs.io/en/stable/parser.html>`__
                - |False|: written as |str|

            .. seealso::
                :ref:`example-type-hint-js`
    """

    FORMAT_NAME = "javascript"
    __VALID_VAR_DECLARATION = ("var", "let", "const")
    __NONE_VALUE_DP = DataProperty("null")

    @property
    def format_name(self):
        return self.FORMAT_NAME

    @property
    def support_split_write(self):
        return True

    @property
    def variable_declaration(self):
        return self.__variable_declaration

    @variable_declaration.setter
    def variable_declaration(self, value):
        value = value.strip().lower()
        if value not in self.__VALID_VAR_DECLARATION:
            raise ValueError("declaration must be either var, let or const")

        self.__variable_declaration = value

    def __init__(self):
        super(JavaScriptTableWriter, self).__init__()

        self.variable_declaration = "const"
        self._dp_extractor.type_value_map = {
            # Typecode.NONE: "null",
            Typecode.INFINITY: "Infinity",
            Typecode.NAN: "NaN",
        }
        self._dp_extractor.strict_level_map[Typecode.BOOL] = StrictLevel.MAX
        self.register_trans_func(bool_to_str)

    def get_variable_name(self, value):
        return sanitize_js_var_name(value, "_").lower()

    def _write_table(self):
        if self.is_datetime_instance_formatting:
            self._dp_extractor.datetime_formatter = js_datetime_formatter
        else:
            self._dp_extractor.datetime_formatter = quote_datetime_formatter

        org_stream = self.stream
        self.stream = six.StringIO()

        self.inc_indent_level()
        super(JavaScriptTableWriter, self)._write_table()
        self.dec_indent_level()
        js_matrix_var_def_text = self.stream.getvalue().rstrip("\n")
        js_matrix_var_def_text = strip_quote(js_matrix_var_def_text, "true")
        js_matrix_var_def_text = strip_quote(js_matrix_var_def_text, "false")
        if self.is_write_closing_row:
            js_matrix_var_def_line_list = js_matrix_var_def_text.splitlines()
            js_matrix_var_def_line_list[-2] = js_matrix_var_def_line_list[-2].rstrip(",")
            js_matrix_var_def_text = "\n".join(js_matrix_var_def_line_list)

        self.stream.close()
        self.stream = org_stream

        self.dec_indent_level()
        self._write_line(js_matrix_var_def_text)
        self.inc_indent_level()

    def _get_opening_row_items(self):
        return ["{:s} {:s} = [".format(self.variable_declaration, self.variable_name)]

    def _get_closing_row_items(self):
        return ["];"]

    def _to_row_item(self, col_dp, value_dp):
        if value_dp.data is None:
            value_dp = self.__NONE_VALUE_DP

        return super(JavaScriptTableWriter, self)._to_row_item(col_dp, value_dp)
