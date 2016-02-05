#!/usr/bin/env python
#
# document generation library

from bcftbx.htmlpagewriter import HTMLPageWriter

class Document:
    """
    Utility class for constructing documents

    """
    def __init__(self,title=None):
        self._title = title
        self._sections = []
        self._css_rules = []

    def add_section(self,title=None,section=None,name=None):
        """
        Add a new section

        """
        if section is None:
            section = Section(title=title,name=name)
        self._sections.append(section)
        return section

    def add_css_rule(self,css_rule):
        """
        """
        self._css_rules.append(css_rule)

    def html(self):
        """
        Generate HTML version of the document contents

        """
        html = []
        if self._title is not None:
            html.append("<h1>%s</h1>" % self._title)
        for section in self._sections:
            try:
                html.append(section.html())
            except AttributeError,ex:
                html.append("<p>Failed to render section: %s</p>" % ex)
        return '\n'.join(html)

    def write(self,outfile):
        """
        Write document contents to a file

        """
        html = HTMLPageWriter(self._title)
        for css_rule in self._css_rules:
            html.addCSSRule(css_rule)
        html.add(self.html())
        html.write("%s" % outfile)

class Section:
    """
    Class representing a generic document section

    """
    def __init__(self,title=None,name=None,level=2):
        self._title = title
        self._name = name
        self._content = []
        self._css_classes = []
        self._level = level

    def add_css_classes(self,*classes):
        """
        Associate CSS classes with the section

        """
        for css_class in classes:
            self._css_classes.append(css_class)

    def add(self,content):
        """
        Add content to the section

        """
        self._content.append(content)

    def add_subsection(self,title=None,section=None,name=None):
        """
        Add subsection within the section

        """
        if section is None:
            subsection = Section(title=title,name=name,level=self._level+1)
        else:
            subsection = section
        self.add(subsection)
        return subsection

    def html(self):
        """
        Generate HTML version of the section

        """
        div = "<div"
        if self._name:
            div += " id='%s'" % self._name
        if self._css_classes:
            div += " class='%s'" % ' '.join(self._css_classes)
        div += ">"
        html = [div,]
        if self._title is not None:
            html.append("<h%d>%s</h%d>" % (self._level,
                                           self._title,
                                           self._level))
        for content in self._content:
            try:
                html.append(content.html())
            except AttributeError,ex:
                html.append("<p>%s</p>" % str(content))
        html.append('</div>')
        return '\n'.join(html)

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
        self._css_classes = []

    def add_css_classes(self,*classes):
        """
        Associate CSS classes with the section

        """
        for css_class in classes:
            self._css_classes.append(css_class)

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

    def html(self,css_id=None):
        """
        Generate HTML version of the table contents

        """
        html = []
        # Opening tag
        table_tag = []
        table_tag.append("<table")
        if css_id is not None:
            table_tag.append(" id='%s'" % css_id)
        if self._css_classes:
            table_tag.append(" class='%s'" % ' '.join(self._css_classes))
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
                    value = row[col].html()
                except KeyError:
                    value = '&nbsp;'
                except AttributeError:
                    value = row[col]
                line.append("<td>%s</td>" % value)
            line.append("</tr>")
            html.append(''.join(line))
        # Finish
        html.append("</table>")
        return '\n'.join(html)

class Img:
    """
    Utility class for embedding <img> tags

    Example usage:

    >>> img = Img('picture.png',width=150)

    """
    def __init__(self,src,height=None,width=None,href=None):
        """
        Create a new ReportTable instance

        Arguments:
          src (str): string to use as the 'src'
            attribute for the <img.../> tag
          height (int): optional height (pixels)
          width (int): optional width (pixels)
          href (str): if specified then the <img.../>
            will be wrapped in <a href..>...</a> with
            this used as the link target

        """
        self._src = src
        self._height = height
        self._width = width
        self._name = None
        self._href = None

    def html(self):
        """
        Generate HTML version of the image tag

        """
        # Build the tag contents
        html = []
        html.append("<img ")
        if self._name:
            html.append("id='%s'" % self._name)
        html.append("src='%s'" % self._src)
        # Optional height and width
        if self._height:
            html.append("height='%s'" % self._height)
        if self._width:
            html.append("width='%s'" % self._width)
        html.append("/>")
        # Wrap in a hef
        if self._href:
            html.insert(0,"<a href='%s'>" % self._href)
            html.append("</a>")
        return " ".join(html)
