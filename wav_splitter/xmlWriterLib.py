# -*- coding: iso-8859-1 -*-

import string
import codecs

from miscLib import uopen, uclose


class NestedElement:
    __slots__ = ('father', 'depth', 'xmlWriter')

    def __init__(self):
	self.father = None
	self.depth = 0
	self.xmlWriter = None

    # protected:
    def flush(self):
	pass

    def finish(self):
	self.flush()

    # public:
    def write(self, cdataStr):
	pass

    def verbatim(self, cdataStr):
	pass

    def add(self, child):
	child.father = self
	child.depth = self.depth + 1
	child.xmlWriter = self.xmlWriter
	return child

    def close(self):
	self.finish()
	return self.father



class NestedFormattedOutput(NestedElement):
    __slots__ = ('cdataList')

    def __init__(self):
	NestedElement.__init__(self)
	self.cdataList = []

    # protected:
    def flush(self):
	if not self.cdataList:
	    return
	indentStr = (self.depth + 1) * self.xmlWriter.indent
	maxMargin = self.xmlWriter.margin
	cdataIter = iter(self.cdataList)
	cdataItem = cdataIter.next()
	try:
	    while True:
		print >> self.xmlWriter.fd, indentStr + cdataItem,
		margin = len(indentStr) + len(cdataItem) + 1
		cdataItem = cdataIter.next()
		margin += len(cdataItem)
		while margin <= maxMargin:
		    print >> self.xmlWriter.fd, cdataItem,
		    cdataItem = cdataIter.next()
		    margin += len(cdataItem) + 1
		print >> self.xmlWriter.fd
	except StopIteration:
	    print >> self.xmlWriter.fd
	self.cdataList = []

    # public:
    def write(self, cdataStr):
	self.cdataList.extend( [ self.xmlWriter.escape(chunk) for chunk in cdataStr.split() ] )

    def verbatim(self, cdataStr):
	self.cdataList.append(cdataStr)



class FormattedXmlElement(NestedFormattedOutput):
    __slots__ = ('name', 'attr')

##    def formTag(self, element, attr=[]):
##	return self.escape(string.join([element] + map(lambda kv: '%s="%s"' % kv, attr)))

    def buildBeginStr(self):
	if not self.attr:
	    return self.name
	attr = [ elem[0] + '="' + self.xmlWriter.escape(elem[1]) + '"' for elem in self.attr.items() ]
	attr.sort()
	return self.name + ' ' + ' '.join(attr)

    def __init__(self, name, attr):
	NestedFormattedOutput.__init__(self)
	self.name = name
	self.attr = attr
	self.xmlWriter = None
	self.father = None
	self.add = self.plainAdd
	self.finish = self.plainFinish

    def plainAdd(self, child):
	print >> self.xmlWriter.fd, (self.depth * self.xmlWriter.indent) + '<' + self.buildBeginStr() + '>'
	self.add = self.nestedAdd
	self.finish = self.nestedFinish
	return self.add(child)

    def nestedAdd(self, child):
	return NestedFormattedOutput.add(self, child)

    def plainFinish(self):
	indentStr = self.depth * self.xmlWriter.indent
	beginStr = self.buildBeginStr()
	if self.cdataList:
	    cdataStr = ' '.join(self.cdataList)
	    if len(indentStr) + len(beginStr) + len(self.name) + len(cdataStr) + 7 <= self.xmlWriter.margin:
		print >> self.xmlWriter.fd, indentStr + '<' + beginStr + '>', cdataStr, '</' + self.name + '>'
	    else:
		print >> self.xmlWriter.fd, indentStr + '<' + beginStr + '>'
		self.flush()
		print >> self.xmlWriter.fd, indentStr + '</' + self.name + '>'
	else:
	    print >> self.xmlWriter.fd, indentStr + '<' + beginStr + '/>'

    def nestedFinish(self):
	self.flush()
	indentStr = self.depth * self.xmlWriter.indent
	print >> self.xmlWriter.fd, indentStr + '</' + self.name + '>'



class FormattedXmlComment(NestedFormattedOutput):
    def __init__(self):
	NestedFormattedOutput.__init__(self)
	self.xmlWriter = None
	self.father = None
	self.add = self.plainAdd
	self.finish = self.plainFinish

    def write(self, cdataStr):
	NestedFormattedOutput.write(self, cdataStr.replace('--', '='))

    def plainAdd(self, child):
	print >> self.xmlWriter.fd, self.buildIdentStr() + '<!--'
	self.add = self.nestedAdd
	self.finish = self.nestedFinish
	return self.add(child)

    def nestedAdd(self, child):
	return NestedFormattedOutput.add(self, child)

    def plainFinish(self):
	if self.cdataList:
	    indentStr = (self.depth * self.xmlWriter.indent)
	    cdataStr = ' '.join(self.cdataList)
	    if len(indentStr) + len(cdataStr) + 9 <= self.xmlWriter.margin:
		print >> self.xmlWriter.fd, indentStr + '<!--', cdataStr, '-->'
	    else:
		print >> self.xmlWriter.fd, indentStr + '<!--'
		self.flush()
		print >> self.xmlWriter.fd, indentStr + '-->'

    def nestedFinish(self):
	self.flush()
	indentStr = self.depth * self.xmlWriter.indent
	print >> self.xmlWriter.fd, indentStr + '-->'



class ClosingXmlElement(NestedElement):
    __slots__ = ('name')

    def __init__(self, name):
	NestedElement.__init__(self)
	self.name = name

    def finish(self):
	self.flush()
	indentStr = self.depth * self.xmlWriter.indent
	print >> self.xmlWriter.fd, indentStr + '</' + self.name + '>'



class XmlRoot:
    def __init__(self, xmlWriter):
	self.xmlWriter = xmlWriter
	self.father = None
	self.finish = self.error
	self.write = self.error
	self.verbatim = self.error
	self.close = self.error

    def error(self, *args1, **args2):
	assert False

    def add(self, child):
	# self.add = self.error
	child.father = self
	child.depth = 0
	child.xmlWriter = self.xmlWriter
	return child



class XmlHeader(XmlRoot):
    def add(self, child):
	print >> self.xmlWriter.fd, '<?xml version="1.0" encoding="' + self.xmlWriter.encoding + '"?>'
	return XmlRoot.add(self, child)



class XmlWriter:
    def __init__(self, fd, encoding):
	self.fd = fd
	self.encoding = encoding
	self.fd = fd
	self.indent = '  '
	self.margin = 78
	self.elem = XmlHeader(self)

    def escape(self, data):
	return data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def setMargin(self, margin):
	self.margin = margin

    def setIndent(self, indent):
	self.indent = indent

    def write(self, cdata):
	self.elem.write(cdata)

    def verbatim(self, cdata):
	self.elem.verbatim(cdata)

    def open(self, element, args = None, **args2):
	if not args: args = args2
	self.elem = self.elem.add(FormattedXmlElement(element, args))

    def close(self):
	self.elem = self.elem.close()

    def element(self, element, cdata=None, **args):
	self.open(element, **args)
	if cdata is not None:
	    self.write(cdata)
	self.close()

    def empty(self, element, args = None, **args2):
	self.open(element, args, **args2)
	self.close()

    def openComment(self):
	self.elem = self.elem.add(FormattedXmlComment())

    def closeComment(self):
	self.close()

    def comment(self, comment):
	self.openComment()
	self.write(comment)
	self.closeComment()



class XmlAppendWriter(XmlWriter):
    def __init__(self, fd, rootElement, encoding):
	XmlWriter.__init__(self, fd, encoding)
	self.elem = XmlRoot(self)
	self.elem = self.elem.add(ClosingXmlElement(rootElement))



def openXml(filename, encoding = 'utf-8'):
    xml = XmlWriter(uopen(filename, encoding, 'w'), encoding)
    return xml


def closeXml(xml):
    assert xml.elem.father is None
    uclose(xml.fd)


def suspendXml(xml):
    assert xml.elem.father is not None and xml.elem.father.father is None
    uclose(xml.fd)


def continueXml(filename, rootElement, encoding = 'utf-8'):
    xml = XmlAppendWriter(uopen(filename, encoding, 'a'), rootElement, encoding)
    return xml
