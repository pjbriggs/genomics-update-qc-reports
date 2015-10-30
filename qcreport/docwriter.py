#!/usr/bin/env python
#
# document generation library


class Table:
    """
    Utility class for constructing tables for output

    Example usage:

    >>> t = Table('Key','Value')

    """
    def __init__(self,columns,**kws):
        """
        Create a new ReportTable instance

        Arguments:
          columns (list): list of column ids
          kws (mapping): optional, mapping of
            column ids to actual names

        """
        self._columns = [x for x in columns]
        self._rows = []
        self._column_names = dict(kws)

    def append_columns(self,*columns,**kws):
        """
        Add a new columns to the table

        Arguments:
          columns (list): list of column ids
          kws (mapping): optional, mapping of
            column ids to actual names

        """
        for col in columns:
            if col in self._columns:
                raise KeyError("Column with id '%s' already defined"
                               % col)
            self._columns.append(col)
        for col in kws:
            self._column_names[col] = kws[col]

    def add_row(self,**kws):
        """
        Add a row to the table

        """
        self._rows.append({})
        n = len(self._rows)-1
        for key in kws:
            self.set_value(n,key,kws[key])
        return n

    def set_value(self,row,key,value):
        """
        Set the value of a field in a row

        """
        if key not in self._columns:
            raise KeyError("Key '%s' not found" % key)
        self._rows[row][key] = value

    def html(self,css_class=None,css_id=None):
        """
        Generate HTML version of the table contents

        """
        html = []
        # Opening tag
        table_tag = []
        table_tag.append("<table")
        if css_id is not None:
            table_tag.append(" id='%s'" % css_id)
        if css_class is not None:
            table_tag.append(" class='%s'" % css_class)
        table_tag.append(">\n")
        html.append(''.join(table_tag))
        # Header
        header = []
        header.append("<tr>")
        for col in self._columns:
            try:
                col_name = self._column_names[col]
            except KeyError:
                col_name = col
            header.append("<th>%s</th>" % col_name)
        header.append("</tr>")
        html.append(''.join(header))
        # Body
        for row in self._rows:
            line = []
            line.append("<tr>")
            for col in self._columns:
                try:
                    value = row[col]
                except KeyError:
                    value = '&nbsp;'
                line.append("<td>%s</td>" % value)
            line.append("</tr>")
            html.append(''.join(line))
        # Finish
        html.append("</table>")
        return '\n'.join(html)
